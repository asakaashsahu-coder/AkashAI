import asyncio
import os
import tempfile
import threading

import edge_tts
import pygame


class Voice:

    def __init__(self, status_callback=None):
        self.voice = "en-US-AriaNeural"
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
    # SPEAK
    # ==================================================

    def speak(self, text, on_finish=None):
        if not text:
            return

        self.stop(update_status=False)

        with self.lock:
            self.is_speaking = True

        self._set_status("Speaking")

        thread = threading.Thread(
            target=self._speak_thread,
            args=(text, on_finish),
            daemon=True
        )
        thread.start()

    def _speak_thread(self, text, on_finish=None):
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
                self._generate_audio(text, temp_file)
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

    async def _generate_audio(self, text, filename):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate="+8%"
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
