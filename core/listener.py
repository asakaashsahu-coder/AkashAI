import threading
import time

import numpy as np
import sounddevice as sd
import speech_recognition as sr


class Listener:

    def __init__(self):
        self.recognizer = sr.Recognizer()

        self.sample_rate = 16000
        self.channels = 1

        self.block_duration = 0.05
        self.silence_limit = 0.65
        self.max_recording_time = 12
        self.start_timeout = 5

        # Starting point for the adaptive microphone threshold.
        self.minimum_volume_threshold = 220
        self.noise_multiplier = 2.8

        self.cancel_event = threading.Event()
        self.last_error = ""

    # ==================================================
    # CONTROL
    # ==================================================

    def cancel(self):
        self.cancel_event.set()

    def reset_cancel(self):
        self.cancel_event.clear()

    # ==================================================
    # RECORD AUDIO
    # ==================================================

    def _record(self, max_time=None, start_timeout=None):
        self.reset_cancel()

        if max_time is None:
            max_time = self.max_recording_time

        if start_timeout is None:
            start_timeout = self.start_timeout

        audio_data = []
        ambient_levels = []

        silence_time = 0
        started_speaking = False
        total_time = 0

        block_size = int(
            self.sample_rate * self.block_duration
        )

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=block_size
        ) as stream:

            while total_time < max_time:
                if self.cancel_event.is_set():
                    return None

                data, overflowed = stream.read(block_size)

                if overflowed:
                    print("Microphone buffer overflow detected.")

                volume = float(
                    np.abs(data.astype(np.float32)).mean()
                )

                # Learn a small amount of background noise before speech starts.
                if not started_speaking and total_time < 0.6:
                    ambient_levels.append(volume)

                if ambient_levels:
                    ambient = sum(ambient_levels) / len(ambient_levels)
                    threshold = max(
                        self.minimum_volume_threshold,
                        ambient * self.noise_multiplier
                    )
                else:
                    threshold = self.minimum_volume_threshold

                if volume > threshold:
                    started_speaking = True
                    silence_time = 0
                    audio_data.append(data.copy())

                elif started_speaking:
                    audio_data.append(data.copy())
                    silence_time += self.block_duration

                total_time += self.block_duration

                # Stop waiting when the user never starts speaking.
                if (
                    not started_speaking
                    and total_time >= start_timeout
                ):
                    break

                # Once speech has started, stop after a natural pause.
                if (
                    started_speaking
                    and silence_time >= self.silence_limit
                ):
                    break

        if not audio_data or not started_speaking:
            return None

        audio_array = np.concatenate(
            audio_data,
            axis=0
        )

        return sr.AudioData(
            audio_array.tobytes(),
            self.sample_rate,
            2
        )

    # ==================================================
    # NORMAL LISTENING
    # ==================================================

    def listen(self):
        self.last_error = ""

        try:
            print("🎤 Listening...")

            audio = self._record()

            if audio is None:
                if self.cancel_event.is_set():
                    self.last_error = "cancelled"
                else:
                    self.last_error = "no_speech"
                return ""

            print("🧠 Processing speech...")

            text = self.recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            text = text.strip()

            print("You said:", text)

            return text

        except sr.UnknownValueError:
            self.last_error = "not_understood"
            print("❌ Speech not understood.")
            return ""

        except sr.RequestError as e:
            self.last_error = "service_error"
            print("❌ Speech recognition error:", e)
            return ""

        except Exception as e:
            self.last_error = "microphone_error"
            print("❌ Microphone error:", e)
            return ""

    # ==================================================
    # WAKE PHRASE
    # ==================================================

    def listen_for_wake_word(self):
        self.last_error = ""

        try:
            audio = self._record(
                max_time=4,
                start_timeout=3
            )

            if audio is None:
                return False

            text = self.recognizer.recognize_google(
                audio,
                language="en-IN"
            ).lower().strip()

            print("Wake listener heard:", text)

            wake_words = [
                "hey jeroo",
                "hey jerro",
                "hey jaroo",
                "jeroo",
                "jerro",
                "jaroo"
            ]

            return any(
                wake_word in text
                for wake_word in wake_words
            )

        except sr.UnknownValueError:
            return False

        except sr.RequestError as e:
            self.last_error = "service_error"
            print("❌ Wake-word recognition error:", e)
            time.sleep(1)
            return False

        except Exception as e:
            self.last_error = "microphone_error"
            print("❌ Wake-word error:", e)
            time.sleep(1)
            return False
