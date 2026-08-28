import asyncio
import os
import re
import tempfile
import threading

import edge_tts
import pygame


class Voice:

    def __init__(self, status_callback=None):
        self.voice = "en-US-AndrewNeural"
        self.is_speaking = False
        self.current_file = None
        self.status_callback = status_callback

        self.lock = threading.Lock()

        pygame.mixer.init()

    # ==================================================
    # STATUS
    # ==================================================

    def _set_status(self, status):
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception:
                pass

    # ==================================================
    # SPEECH TEXT CLEANER
    # ==================================================

    def clean_for_speech(self, text):
        """
        Convert display/Markdown text into natural spoken text.
        The original response shown in the chat is not changed.
        """

        text = str(text or "")

        if not text.strip():
            return ""

        # Code fences and Markdown links/images.
        text = re.sub(
            r"```(?:[a-zA-Z0-9_+-]+)?",
            "",
            text
        )

        text = re.sub(
            r"!\[([^\]]*)\]\((?:[^)]+)\)",
            r"\1",
            text
        )

        text = re.sub(
            r"\[([^\]]+)\]\((?:[^)]+)\)",
            r"\1",
            text
        )

        # Raw URLs are unpleasant when read aloud.
        text = re.sub(
            r"https?://\S+",
            "",
            text
        )

        # Headings, quotes, bullets and separators.
        text = re.sub(
            r"(?m)^\s{0,3}#{1,6}\s*",
            "",
            text
        )

        text = re.sub(
            r"(?m)^\s*>\s?",
            "",
            text
        )

        text = re.sub(
            r"(?m)^\s*[-+*]\s+",
            "",
            text
        )

        text = re.sub(
            r"(?m)^\s*(\d+)[.)]\s+",
            r"\1. ",
            text
        )

        text = re.sub(
            r"(?m)^\s*[-_=]{3,}\s*$",
            "",
            text
        )

        # Markdown emphasis and inline-code characters.
        for token in (
            "**",
            "__",
            "~~",
            "`",
            "*",
            "#",
        ):
            text = text.replace(
                token,
                ""
            )

        # Visual bullets/symbols that should not be spoken.
        text = re.sub(
            r"[•●▪◦◆◇■□▶►]+",
            " ",
            text
        )

        # Clean spacing/punctuation for more natural speech.
        text = re.sub(
            r"[!]{2,}",
            "!",
            text
        )

        text = re.sub(
            r"[?]{2,}",
            "?",
            text
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        text = re.sub(
            r"\n\s*\n+",
            "\n",
            text
        )

        text = re.sub(
            r"\s*\n\s*",
            ". ",
            text
        )

        text = re.sub(
            r"\.{2,}",
            ".",
            text
        )

        text = re.sub(
            r"\s+([,.!?;:])",
            r"\1",
            text
        )

        text = re.sub(
            r"\s{2,}",
            " ",
            text
        )

        # Natural speech shaping.
        # This only affects what Jerro says, not what appears in chat.

        # Normal comma / semicolon pacing.
        text = re.sub(
            r",\s*",
            ", ",
            text
        )

        text = re.sub(
            r";\s*",
            "; ",
            text
        )

        # Make sentence boundaries clear without creating robotic gaps.
        text = re.sub(
            r"([.!?])\s+",
            r"\1 ",
            text
        )

        # Convert common visual separators into spoken pauses.
        text = re.sub(
            r"\s*[—–]\s*",
            ", ",
            text
        )

        # Avoid TTS sounding mechanical on repeated punctuation.
        text = re.sub(
            r"!{2,}",
            "!",
            text
        )

        text = re.sub(
            r"\?{2,}",
            "?",
            text
        )

        # Friendly contractions sound more natural than formal expansions.
        replacements = {
            "do not": "don't",
            "does not": "doesn't",
            "did not": "didn't",
            "cannot": "can't",
            "will not": "won't",
            "it is": "it's",
            "that is": "that's",
            "you are": "you're",
            "we are": "we're",
            "I am": "I'm",
        }

        for old, new in replacements.items():
            text = re.sub(
                rf"\b{re.escape(old)}\b",
                new,
                text,
                flags=re.IGNORECASE
            )

        return text.strip()

    # ==================================================
    # EMOTION / PROSODY
    # ==================================================

    def detect_emotion(self, text, context=None):
        """Pick a light speaking style from the reply and user context."""

        reply = str(text or "").strip().lower()
        user_context = str(context or "").strip().lower()
        value = f"{user_context} {reply}".strip()

        if not value:
            return "neutral"

        # The user's message matters as much as the reply.
        # This lets Jeroo react naturally even when the generated reply
        # itself does not contain an obvious emotion keyword.
        if any(word in user_context for word in (
            "i'm scared", "im scared", "i am scared",
            "worried", "nervous", "stressed", "anxious",
            "i feel bad", "feeling bad", "sad", "upset"
        )):
            return "reassuring"

        if any(word in user_context for word in (
            "finally worked", "it worked", "we did it",
            "i did it", "got it working", "success",
            "awesome", "amazing", "let's go", "lets go"
        )):
            return "excited"

        if any(word in user_context for word in (
            "why", "how come", "what if", "do you think",
            "i wonder", "not sure", "confused", "hmm"
        )):
            return "curious"

        if any(word in user_context for word in (
            "error", "problem", "issue", "not working",
            "failed", "wrong", "danger", "risk"
        )):
            return "concerned"

        if any(word in value for word in (
            "congrat", "awesome", "great!", "nice!",
            "amazing", "perfect!", "we did it", "worked!"
        )):
            return "excited"

        if any(word in value for word in (
            "haha", "lol", "funny", "that was close",
            "well, that happened"
        )):
            return "amused"

        if any(word in value for word in (
            "hmm", "interesting", "curious", "i wonder",
            "let me think", "let me check"
        )):
            return "curious"

        if any(word in value for word in (
            "careful", "warning", "problem", "error",
            "failed", "doesn't look right", "not safe",
            "risk", "issue"
        )):
            return "concerned"

        if any(word in value for word in (
            "don't worry", "it'll be okay", "we can fix",
            "take your time", "no rush", "i've got you"
        )):
            return "reassuring"

        if any(word in value for word in (
            "important", "serious", "must", "do not",
            "critical", "security"
        )):
            return "serious"

        return "neutral"

    def get_voice_profile(self, emotion):
        profiles = {
            "neutral": {
                "rate": "-6%",
                "pitch": "-2Hz",
                "volume": "+0%"
            },
            "excited": {
                "rate": "+3%",
                "pitch": "+3Hz",
                "volume": "+2%"
            },
            "amused": {
                "rate": "-1%",
                "pitch": "+2Hz",
                "volume": "+1%"
            },
            "curious": {
                "rate": "-8%",
                "pitch": "+1Hz",
                "volume": "+0%"
            },
            "concerned": {
                "rate": "-12%",
                "pitch": "-4Hz",
                "volume": "-1%"
            },
            "reassuring": {
                "rate": "-11%",
                "pitch": "-3Hz",
                "volume": "+0%"
            },
            "serious": {
                "rate": "-10%",
                "pitch": "-5Hz",
                "volume": "+0%"
            },
        }

        return profiles.get(
            emotion,
            profiles["neutral"]
        )

    # ==================================================
    # SPEAK
    # ==================================================

    def speak(self, text, on_finish=None, context=None):
        if not text:
            return

        speech_text = self.clean_for_speech(
            text
        )

        emotion = self.detect_emotion(text, context=context)

        if not speech_text:
            if on_finish:
                try:
                    on_finish()
                except Exception:
                    pass
            return

        self.stop(update_status=False)

        with self.lock:
            self.is_speaking = True

        self._set_status("Speaking")

        thread = threading.Thread(
            target=self._speak_thread,
            args=(speech_text, emotion, on_finish),
            daemon=True
        )
        thread.start()

    def _speak_thread(self, text, emotion="neutral", on_finish=None):
        temp_file = None

        try:
            temp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp3"
            )
            temp_file = temp.name
            temp.close()

            self.current_file = temp_file

            asyncio.run(
                self._generate_audio(text, temp_file, emotion)
            )

            with self.lock:
                should_speak = self.is_speaking

            if not should_speak:
                return

            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            clock = pygame.time.Clock()

            while pygame.mixer.music.get_busy():
                with self.lock:
                    still_speaking = self.is_speaking

                if not still_speaking:
                    pygame.mixer.music.stop()
                    break

                clock.tick(20)

        except Exception as e:
            print(f"Voice error: {e}")

        finally:
            with self.lock:
                self.is_speaking = False

            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass

            if temp_file:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass

            self.current_file = None
            self._set_status("Ready")

            if on_finish:
                try:
                    on_finish()
                except Exception as e:
                    print("Voice finish callback error:", e)

    async def _generate_audio(self, text, filename, emotion="neutral"):
        profile = self.get_voice_profile(emotion)

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=profile["rate"],
            pitch=profile["pitch"],
            volume=profile["volume"]
        )
        await communicate.save(filename)

    # ==================================================
    # STOP / INTERRUPTION
    # ==================================================

    def stop(self, update_status=True):
        with self.lock:
            self.is_speaking = False

        try:
            pygame.mixer.music.stop()

            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

        except Exception:
            pass

        if update_status:
            self._set_status("Ready")

    def speaking(self):
        with self.lock:
            return self.is_speaking
