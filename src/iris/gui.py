import threading
import tkinter as tk

from torch import multiprocessing as mp

from iris.data_types import (OutputChannel, ProcessArgs, RecorderState,
                             TranscriptionMsg, TTSMsg)


class Subtitle:
    num_lines = 6

    def __init__(self):
        self.lines = ["" for i in range(self.num_lines)]

    def add(self, text):
        self.lines.append(text)
        if len(self.lines) > self.num_lines:
            self.lines.pop(0)

    def __str__(self) -> str:
        return "\n".join(self.lines[::-1])


class UserInterface:
    def __init__(self, ui_update_q: mp.Queue):
        self.root = tk.Tk()
        self.subtitles = Subtitle()
        self.ui_update_q = ui_update_q

        self.init_gui()

    def init_gui(self):
        self.root.title("IRIS")

        canvas_width, canvas_height = 800, 600
        self.root.geometry(f"{canvas_width}x{canvas_height}")
        self.root.configure(background="black")
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)
        label_font_size = 18

        self.subtitle_label = tk.Label(
            self.root,
            text=str(self.subtitles),
            justify="center",
            font=("Arial", label_font_size),
            fg="white",
            bg=self.root.cget("background"),
            wraplength=1000,
        )

        self.tts_label = tk.Label(
            self.root,
            text="sub",
            justify="center",
            font=("Arial", 14),
            fg="white",
            bg=self.root.cget("background"),
            wraplength=1000,
        )

        self.subtitle_label.grid(row=2, column=1, sticky=tk.S)
        # self.realtime_label.grid(row=1, column=1, sticky=tk.S)

        self.status_indicator = tk.Canvas(
            self.root,
            width=25,
            height=25,
            bg=self.root.cget("background"),
            highlightthickness=0,
        )

        self.status_indicator.place(relx=0.01, y=5)
        self.tts_label.place(relx=0.95, y=5)
        self.root.bind("<space>", lambda x: self.toggle_tts())
        self.set_recording_status(RecorderState.OFFLINE)

    def set_recording_status(self, state: RecorderState):
        status_map = {
            RecorderState.RECORDING: "#ffff00",
            RecorderState.OFFLINE: "#ff0000",
            RecorderState.LISTENING: "#00ff00",
        }
        self.status_indicator.delete("all")
        self.status_indicator.create_oval(
            0, 0, 20, 20, fill=status_map.get(state, "#000000")
        )

    def toggle_tts(self):
        self.ui_update_q.put({"toggle_tts": {}})

    def add_subtitles(self, text):
        self.subtitles.add(text)
        self.subtitle_label["text"] = str(self.subtitles)

    def run(self):
        self.root.mainloop()
