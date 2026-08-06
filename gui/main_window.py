import customtkinter as ctk
from core.brain import Brain


class MainWindow:

    def __init__(self):

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.brain = Brain()

        self.app = ctk.CTk()
        self.app.title("🤖 AkashAI")
        self.app.geometry("950x650")

        # ---------- Header ----------
        self.header = ctk.CTkFrame(self.app, height=60)
        self.header.pack(fill="x")

        self.title = ctk.CTkLabel(
            self.header,
            text="🤖 AkashAI",
            font=("Arial", 26, "bold")
        )
        self.title.pack(pady=15)

        # ---------- Chat Box ----------
        self.chat_box = ctk.CTkTextbox(
            self.app,
            wrap="word",
            font=("Arial", 15)
        )

        self.chat_box.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15
        )

        self.chat_box.insert(
            "end",
            "🤖 AkashAI: Hello! I am your personal AI assistant.\n\n"
        )

        self.chat_box.configure(state="disabled")

        # ---------- Bottom ----------
        self.bottom = ctk.CTkFrame(self.app)
        self.bottom.pack(fill="x", padx=20, pady=10)

        self.message_entry = ctk.CTkEntry(
            self.bottom,
            placeholder_text="Ask me anything..."
        )

        self.message_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 10),
            pady=10
        )

        self.message_entry.bind("<Return>", self.send_message_event)

        self.send_button = ctk.CTkButton(
            self.bottom,
            text="Send",
            width=90,
            command=self.send_message
        )

        self.send_button.pack(
            side="right",
            padx=10,
            pady=10
        )

    def send_message_event(self, event):
        self.send_message()

    def send_message(self):

        message = self.message_entry.get().strip()

        if not message:
            return

        self.chat_box.configure(state="normal")

        self.chat_box.insert(
            "end",
            f"👤 You: {message}\n\n"
        )

        self.chat_box.insert(
            "end",
            "🤖 AkashAI: Thinking...\n\n"
        )

        self.chat_box.see("end")
        self.app.update()

        response = self.brain.get_response(message)

        self.chat_box.delete("end-2l", "end")

        self.chat_box.insert(
            "end",
            f"🤖 AkashAI: {response}\n\n"
        )

        self.chat_box.configure(state="disabled")

        self.chat_box.see("end")

        self.message_entry.delete(0, "end")

    def run(self):
        self.app.mainloop()