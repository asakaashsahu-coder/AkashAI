import math
import random
import tkinter as tk

import customtkinter as ctk


class FloatingAssistant(ctk.CTkToplevel):

    def __init__(
        self,
        parent,
        restore_callback,
        exit_callback,
        wake_callback,
        voice_chat_callback
    ):
        super().__init__(parent)

        self.parent = parent
        self.restore_callback = restore_callback
        self.exit_callback = exit_callback
        self.wake_callback = wake_callback
        self.voice_chat_callback = voice_chat_callback

        # ==================================================
        # WINDOW
        # ==================================================

        self.size = 126
        self.transparent_key = "#010203"

        self.geometry(
            f"{self.size}x{self.size}"
        )

        self.resizable(
            False,
            False
        )

        self.overrideredirect(
            True
        )

        self.attributes(
            "-topmost",
            True
        )

        self.configure(
            fg_color=self.transparent_key
        )

        # Windows transparent color.
        try:
            self.wm_attributes(
                "-transparentcolor",
                self.transparent_key
            )
        except Exception:
            pass

        # ==================================================
        # DRAG STATE
        # ==================================================

        self.drag_x = 0
        self.drag_y = 0
        self.dragged = False

        # ==================================================
        # ORB STATE
        # ==================================================

        self.status = "Ready"

        self.phase = 0.0
        self.rotation = 0.0
        self.hover_amount = 0.0
        self.hovered = False
        self.running = True
        self.shutting_down = False

        self.energy = 0.0

        self.state_colors = {
            "Ready": {
                "core": "#147DFF",
                "bright": "#63E6FF",
                "outer": "#6C4DFF"
            },

            "Listening": {
                "core": "#00B887",
                "bright": "#62FFD6",
                "outer": "#00E5B0"
            },

            "Thinking": {
                "core": "#D18A00",
                "bright": "#FFD866",
                "outer": "#FFAA19"
            },

            "Speaking": {
                "core": "#7C3AED",
                "bright": "#D7A4FF",
                "outer": "#B968FF"
            },

            "Wake Listening": {
                "core": "#D81B60",
                "bright": "#FF8CBC",
                "outer": "#FF3D8F"
            },

            "Reminder": {
                "core": "#E11D48",
                "bright": "#FFE4E6",
                "outer": "#FB7185"
            },

            "Error": {
                "core": "#374151",
                "bright": "#FFFFFF",
                "outer": "#D1D5DB"
            },

            "Starting": {
                "core": "#155EEF",
                "bright": "#72D2FF",
                "outer": "#7C65FF"
            }
        }

        # ==================================================
        # POSITION
        # ==================================================

        self.update_idletasks()

        x = max(
            20,
            self.winfo_screenwidth()
            - self.size
            - 28
        )

        y = max(
            20,
            self.winfo_screenheight()
            - self.size
            - 92
        )

        self.geometry(
            f"{self.size}x{self.size}+{x}+{y}"
        )

        # ==================================================
        # CANVAS
        # ==================================================

        self.canvas = tk.Canvas(
            self,
            width=self.size,
            height=self.size,
            highlightthickness=0,
            bd=0,
            bg=self.transparent_key
        )

        self.canvas.pack(
            fill="both",
            expand=True
        )

        # ==================================================
        # PARTICLES
        # ==================================================

        random.seed(7)

        self.particles = []

        for _ in range(15):
            self.particles.append({
                "angle": random.uniform(
                    0,
                    math.tau
                ),
                "radius": random.uniform(
                    40,
                    53
                ),
                "speed": random.uniform(
                    0.004,
                    0.014
                ),
                "size": random.uniform(
                    1.0,
                    2.4
                ),
                "offset": random.uniform(
                    0,
                    math.tau
                )
            })

        # ==================================================
        # EVENTS
        # ==================================================

        self.canvas.bind(
            "<ButtonPress-1>",
            self._drag_start
        )

        self.canvas.bind(
            "<B1-Motion>",
            self._drag_move
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self._drag_end
        )

        self.canvas.bind(
            "<Double-Button-1>",
            self._restore
        )

        self.canvas.bind(
            "<Button-3>",
            self._show_menu
        )

        self.canvas.bind(
            "<Enter>",
            self._on_enter
        )

        self.canvas.bind(
            "<Leave>",
            self._on_leave
        )

        # ==================================================
        # RIGHT CLICK MENU
        # ==================================================

        self.menu = tk.Menu(
            self,
            tearoff=0,
            bg="#0B1220",
            fg="#EEF4FF",
            activebackground="#1A2740",
            activeforeground="#FFFFFF",
            borderwidth=0,
            relief="flat",
            font=(
                "Segoe UI",
                10
            )
        )

        self.menu.add_command(
            label="Open Jerro",
            command=self._restore
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="Toggle Wake Mode",
            command=self._toggle_wake
        )

        self.menu.add_command(
            label="Toggle Voice Chat",
            command=self._toggle_voice_chat
        )

        self.menu.add_separator()

        self.menu.add_command(
            label="Exit Jerro",
            command=self.exit_callback
        )

        # ==================================================
        # START
        # ==================================================

        self.withdraw()

        self.after(
            16,
            self._animate
        )

    # ==================================================
    # COLOR
    # ==================================================

    def _hex_to_rgb(
        self,
        color
    ):
        color = color.lstrip("#")

        return tuple(
            int(
                color[index:index + 2],
                16
            )
            for index in (
                0,
                2,
                4
            )
        )

    def _rgb_to_hex(
        self,
        rgb
    ):
        return "#{:02x}{:02x}{:02x}".format(
            *[
                max(
                    0,
                    min(
                        255,
                        int(value)
                    )
                )
                for value in rgb
            ]
        )

    def _mix(
        self,
        first,
        second,
        amount
    ):
        amount = max(
            0.0,
            min(
                1.0,
                amount
            )
        )

        a = self._hex_to_rgb(
            first
        )

        b = self._hex_to_rgb(
            second
        )

        return self._rgb_to_hex(
            tuple(
                a[index]
                + (
                    b[index]
                    - a[index]
                )
                * amount
                for index in range(3)
            )
        )

    # ==================================================
    # DRAWING
    # ==================================================

    def _draw(self):
        self.canvas.delete(
            "all"
        )

        center = self.size / 2

        colors = self.state_colors.get(
            self.status,
            self.state_colors[
                "Ready"
            ]
        )

        core = colors[
            "core"
        ]

        bright = colors[
            "bright"
        ]

        outer = colors[
            "outer"
        ]

        pulse = (
            math.sin(
                self.phase
            )
            + 1
        ) / 2

        slow_pulse = (
            math.sin(
                self.phase * 0.48
            )
            + 1
        ) / 2

        hover_scale = (
            1
            + self.hover_amount * 0.06
        )

        # ==================================================
        # AMBIENT GLOW
        # ==================================================

        glow_radii = [
            (
                57,
                0.08
            ),
            (
                53,
                0.13
            ),
            (
                49,
                0.20
            ),
            (
                45,
                0.29
            )
        ]

        for radius, intensity in glow_radii:

            animated = (
                radius
                + pulse * 3.2
            ) * hover_scale

            glow_color = self._mix(
                self.transparent_key,
                outer,
                intensity
            )

            self.canvas.create_oval(
                center - animated,
                center - animated,
                center + animated,
                center + animated,
                fill=glow_color,
                outline=""
            )

        # ==================================================
        # PARTICLES
        # ==================================================

        for particle in self.particles:

            particle[
                "angle"
            ] += particle[
                "speed"
            ]

            radius = (
                particle[
                    "radius"
                ]
                + math.sin(
                    self.phase * 0.8
                    + particle[
                        "offset"
                    ]
                ) * 2.5
            )

            x = (
                center
                + math.cos(
                    particle[
                        "angle"
                    ]
                ) * radius
            )

            y = (
                center
                + math.sin(
                    particle[
                        "angle"
                    ]
                ) * radius
            )

            particle_size = (
                particle[
                    "size"
                ]
                * (
                    0.75
                    + pulse * 0.45
                )
            )

            particle_color = self._mix(
                outer,
                "#FFFFFF",
                0.30
            )

            self.canvas.create_oval(
                x - particle_size,
                y - particle_size,
                x + particle_size,
                y + particle_size,
                fill=particle_color,
                outline=""
            )

        # ==================================================
        # OUTER ENERGY RING
        # ==================================================

        ring_radius = (
            42
            + slow_pulse * 2.2
        ) * hover_scale

        self.canvas.create_oval(
            center - ring_radius,
            center - ring_radius,
            center + ring_radius,
            center + ring_radius,
            outline=self._mix(
                outer,
                "#FFFFFF",
                0.10
            ),
            width=2
        )

        # Rotating broken ring.
        for index in range(3):

            start = (
                self.rotation
                + index * 120
            )

            extent = (
                58
                + math.sin(
                    self.phase
                    + index
                ) * 11
            )

            self.canvas.create_arc(
                center - 47,
                center - 47,
                center + 47,
                center + 47,
                start=start,
                extent=extent,
                style="arc",
                outline=bright,
                width=2
            )

        # ==================================================
        # CORE BALL
        # ==================================================

        core_radius = (
            34
            + pulse * 1.4
        ) * hover_scale

        # Dark shell.
        self.canvas.create_oval(
            center - core_radius,
            center - core_radius,
            center + core_radius,
            center + core_radius,
            fill="#06101F",
            outline=self._mix(
                outer,
                "#FFFFFF",
                0.28
            ),
            width=2
        )

        # Main colored inner core.
        inner_radius = (
            core_radius - 4
        )

        self.canvas.create_oval(
            center - inner_radius,
            center - inner_radius,
            center + inner_radius,
            center + inner_radius,
            fill=core,
            outline=""
        )

        # ==================================================
        # DEPTH / GLASS SHADING
        # ==================================================

        shade = self._mix(
            core,
            "#000000",
            0.46
        )

        self.canvas.create_arc(
            center - inner_radius,
            center - inner_radius,
            center + inner_radius,
            center + inner_radius,
            start=205,
            extent=150,
            style="pieslice",
            fill=shade,
            outline=""
        )

        # Soft top highlight.
        highlight = self._mix(
            bright,
            "#FFFFFF",
            0.38
        )

        self.canvas.create_oval(
            center - 18,
            center - 22,
            center + 9,
            center + 3,
            fill=highlight,
            outline=""
        )

        # Thin glossy crescent.
        self.canvas.create_arc(
            center - 27,
            center - 27,
            center + 27,
            center + 27,
            start=42,
            extent=92,
            style="arc",
            outline="#FFFFFF",
            width=2
        )

        # ==================================================
        # STATE-SPECIFIC CENTER
        # ==================================================

        if self.status in {
            "Listening",
            "Speaking"
        }:

            self._draw_waveform(
                center,
                bright
            )

        elif self.status == "Thinking":

            self._draw_thinking(
                center,
                bright
            )

        elif self.status == "Wake Listening":

            self._draw_mic(
                center,
                bright
            )

        elif self.status == "Reminder":

            self.canvas.create_text(
                center,
                center,
                text="!",
                fill="#FFFFFF",
                font=(
                    "Segoe UI",
                    28,
                    "bold"
                )
            )

        elif self.status == "Error":

            self.canvas.create_text(
                center,
                center,
                text="!",
                fill="#FFFFFF",
                font=(
                    "Segoe UI",
                    28,
                    "bold"
                )
            )

        else:

            self.canvas.create_text(
                center,
                center + 1,
                text="J",
                fill="#FFFFFF",
                font=(
                    "Segoe UI",
                    29,
                    "bold"
                )
            )

        # ==================================================
        # BOTTOM LIGHT / FLOOR GLOW
        # ==================================================

        floor_width = (
            28
            + pulse * 10
        )

        floor_y = (
            center
            + 47
        )

        self.canvas.create_oval(
            center - floor_width,
            floor_y - 2,
            center + floor_width,
            floor_y + 3,
            fill=self._mix(
                self.transparent_key,
                bright,
                0.34
            ),
            outline=""
        )

    def _draw_waveform(
        self,
        center,
        color
    ):
        bars = [
            8,
            16,
            25,
            34,
            25,
            16,
            8
        ]

        spacing = 5

        total = (
            len(
                bars
            )
            - 1
        ) * spacing

        start_x = (
            center
            - total / 2
        )

        for index, base_height in enumerate(
            bars
        ):

            animated_height = (
                base_height
                * (
                    0.55
                    + (
                        math.sin(
                            self.phase * 2.4
                            + index * 0.9
                        )
                        + 1
                    ) / 4
                )
            )

            x = (
                start_x
                + index * spacing
            )

            self.canvas.create_line(
                x,
                center - animated_height / 2,
                x,
                center + animated_height / 2,
                fill=color,
                width=3,
                capstyle="round"
            )

    def _draw_thinking(
        self,
        center,
        color
    ):
        radius = 12

        for index in range(3):

            angle = (
                self.phase * 1.5
                + index * math.tau / 3
            )

            x = (
                center
                + math.cos(
                    angle
                ) * radius
            )

            y = (
                center
                + math.sin(
                    angle
                ) * radius
            )

            dot_size = (
                3.2
                + (
                    math.sin(
                        self.phase
                        + index
                    )
                    + 1
                ) * 1.2
            )

            self.canvas.create_oval(
                x - dot_size,
                y - dot_size,
                x + dot_size,
                y + dot_size,
                fill=color,
                outline=""
            )

    def _draw_mic(
        self,
        center,
        color
    ):
        self.canvas.create_oval(
            center - 6,
            center - 15,
            center + 6,
            center + 7,
            outline=color,
            width=3
        )

        self.canvas.create_arc(
            center - 11,
            center - 4,
            center + 11,
            center + 13,
            start=180,
            extent=180,
            style="arc",
            outline=color,
            width=3
        )

        self.canvas.create_line(
            center,
            center + 13,
            center,
            center + 20,
            fill=color,
            width=3
        )

        self.canvas.create_line(
            center - 7,
            center + 20,
            center + 7,
            center + 20,
            fill=color,
            width=3
        )

    # ==================================================
    # ANIMATION
    # ==================================================

    def _animate(self):
        if (
            not self.running
            or self.shutting_down
        ):
            return

        self.phase += 0.085
        self.rotation = (
            self.rotation
            + 1.4
        ) % 360

        target_hover = (
            1.0
            if self.hovered
            else 0.0
        )

        self.hover_amount += (
            target_hover
            - self.hover_amount
        ) * 0.15

        try:
            if self.winfo_exists():
                self._draw()

        except Exception:
            return

        self.after(
            16,
            self._animate
        )

    # ==================================================
    # STATUS
    # ==================================================

    def set_status(
        self,
        status,
        color=None
    ):
        self.status = status

    # ==================================================
    # HOVER
    # ==================================================

    def _on_enter(
        self,
        event=None
    ):
        self.hovered = True

    def _on_leave(
        self,
        event=None
    ):
        self.hovered = False

    # ==================================================
    # DRAG
    # ==================================================

    def _drag_start(
        self,
        event
    ):
        self.dragged = False

        self.drag_x = (
            event.x_root
            - self.winfo_x()
        )

        self.drag_y = (
            event.y_root
            - self.winfo_y()
        )

    def _drag_move(
        self,
        event
    ):
        self.dragged = True

        x = (
            event.x_root
            - self.drag_x
        )

        y = (
            event.y_root
            - self.drag_y
        )

        x = max(
            0,
            min(
                x,
                self.winfo_screenwidth()
                - self.winfo_width()
            )
        )

        y = max(
            0,
            min(
                y,
                self.winfo_screenheight()
                - self.winfo_height()
            )
        )

        self.geometry(
            f"+{x}+{y}"
        )

    def _drag_end(
        self,
        event=None
    ):
        pass

    # ==================================================
    # MENU / ACTIONS
    # ==================================================

    def _show_menu(
        self,
        event
    ):
        if self.shutting_down:
            return

        try:
            if not self.winfo_exists():
                return

            self.menu.tk_popup(
                event.x_root,
                event.y_root
            )

        except tk.TclError:
            return

        except Exception as error:
            print(
                "Jerro menu error:",
                error
            )

        finally:
            try:
                if not self.shutting_down:
                    self.menu.grab_release()
            except Exception:
                pass

    def _restore(
        self,
        event=None
    ):
        if self.restore_callback:
            self.restore_callback()

    def _toggle_wake(self):
        if self.wake_callback:
            self.wake_callback()

    def _toggle_voice_chat(self):
        if self.voice_chat_callback:
            self.voice_chat_callback()

    # ==================================================
    # CLEAN SHUTDOWN
    # ==================================================

    def prepare_shutdown(self):
        if self.shutting_down:
            return

        self.shutting_down = True
        self.running = False

        try:
            self.menu.unpost()
        except Exception:
            pass

        try:
            self.withdraw()
        except Exception:
            pass

    # ==================================================
    # SHOW / HIDE
    # ==================================================

    def show(self):
        if self.shutting_down:
            return

        try:
            self.deiconify()
            self.lift()

            self.attributes(
                "-topmost",
                True
            )

        except Exception:
            pass

    def hide(self):
        try:
            self.withdraw()

        except Exception:
            pass

    # ==================================================
    # DESTROY
    # ==================================================

    def destroy(self):
        self.prepare_shutdown()

