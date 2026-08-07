import asyncio
import tempfile
import os
import threading

import edge_tts
import pygame


class Voice:

    def __init__(self):

        self.voice = "en-US-AriaNeural"

        self.is_speaking = False
        self.current_file = None

        pygame.mixer.init()

    # ==================================================
    # SPEAK
    # ==================================================

    def speak(self, text):

        # Stop previous speech
        self.stop()

        self.is_speaking = True

        thread = threading.Thread(
            target=self._speak_thread,
            args=(text,),
            daemon=True
        )

        thread.start()

    # ==================================================
    # SPEAK THREAD
    # ==================================================

    def _speak_thread(self, text):

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
                self._generate_audio(
                    text,
                    temp_file
                )
            )

            # User stopped speech
            if not self.is_speaking:
                return

            pygame.mixer.music.load(
                temp_file
            )

            pygame.mixer.music.play()

            # Monitor playback
            while pygame.mixer.music.get_busy():

                if not self.is_speaking:

                    pygame.mixer.music.stop()

                    break

                pygame.time.Clock().tick(20)

        except Exception as e:

            print(
                f"Voice error: {e}"
            )

        finally:

            self.is_speaking = False

            try:

                pygame.mixer.music.stop()

            except Exception:
                pass

            if temp_file:

                try:

                    if os.path.exists(
                        temp_file
                    ):

                        os.remove(
                            temp_file
                        )

                except Exception:
                    pass

            self.current_file = None

    # ==================================================
    # GENERATE AUDIO
    # ==================================================

    async def _generate_audio(
        self,
        text,
        filename
    ):

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice
        )

        await communicate.save(
            filename
        )

    # ==================================================
    # STOP SPEAKING
    # ==================================================

    def stop(self):

        self.is_speaking = False

        try:

            pygame.mixer.music.stop()

        except Exception:
            pass