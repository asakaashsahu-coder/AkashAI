import sounddevice as sd
import speech_recognition as sr
import numpy as np


class Listener:

    def __init__(self):

        self.recognizer = sr.Recognizer()

        self.sample_rate = 16000
        self.channels = 1

        self.block_duration = 0.05
        self.silence_limit = 0.7
        self.max_recording_time = 7
        self.volume_threshold = 400

    def _record(self, max_time=None):

        if max_time is None:
            max_time = self.max_recording_time

        audio_data = []

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

                data, overflowed = stream.read(
                    block_size
                )

                audio_data.append(data.copy())

                volume = np.abs(
                    data.astype(np.float32)
                ).mean()

                if volume > self.volume_threshold:

                    started_speaking = True
                    silence_time = 0

                elif started_speaking:

                    silence_time += self.block_duration

                total_time += self.block_duration

                if (
                    started_speaking
                    and silence_time >= self.silence_limit
                ):
                    break

        if not audio_data:
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

    def listen(self):

        try:

            print("🎤 Listening...")

            audio = self._record()

            if audio is None:
                return ""

            print("🧠 Processing...")

            text = self.recognizer.recognize_google(
                audio
            )

            print("You said:", text)

            return text

        except sr.UnknownValueError:

            print("❌ Speech not understood.")
            return ""

        except sr.RequestError as e:

            print(
                "❌ Speech recognition error:",
                e
            )

            return ""

        except Exception as e:

            print(
                "❌ Microphone error:",
                e
            )

            return ""

    def listen_for_wake_word(self):

        try:

            print("👂 Listening for 'Hey Jeroo'...")

            # Shorter recording for wake phrase
            audio = self._record(
                max_time=4
            )

            if audio is None:
                return False

            print("🧠 Checking wake word...")

            text = self.recognizer.recognize_google(
                audio
            ).lower().strip()

            print("Heard:", text)

            wake_words = [
                "hey jeroo",
                "hey jeroo",
                "jeroo",
                "jaroo",
                "hey jaroo"
            ]

            return any(
                word in text
                for word in wake_words
            )

        except sr.UnknownValueError:

            return False

        except sr.RequestError as e:

            print(
                "❌ Speech recognition error:",
                e
            )

            return False

        except Exception as e:

            print(
                "❌ Wake-word error:",
                e
            )

            return False