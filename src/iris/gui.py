import tkinter as tk
from iris.data_types import (
    ProcessArgs,
    RecorderState,
    Settings,
    OutputChannel,
    TranscriptionMsg,
    TTSMsg,
    UIStateUpdateMsg,
)
from torch import multiprocessing as mp
import threading


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
    def __init__(
        self, tts_q: mp.Queue, sub_translation, args: ProcessArgs, ui_udate_q: mp.Queue
    ):
        self.root = tk.Tk()
        self.subtitles = Subtitle()
        self.tts_q = tts_q
        self.args = args
        self.ui_udate_q = ui_udate_q

        self.init_gui()
        self.sub_translation = sub_translation

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
            font=("Arial", 12),
            fg="grey",
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

        self.status_indicator.place(relx=0.01, rely=0.95)
        self.tts_label.place(relx=0.95, rely=0.95)
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
        if self.args.is_tts_mode.is_set():
            self.args.ui_update_q.put(UIStateUpdateMsg(set_tts_status=False))
        else:
            self.args.ui_update_q.put(UIStateUpdateMsg(set_tts_status=True))

    def add_subtitles(self, text):
        self.subtitles.add(text)
        self.subtitle_label["text"] = str(self.subtitles)

    def run(self):
        # self.root.bind("<Return>", lambda x: self.recorder.recorder.stop())
        self.root.bind("<space>", lambda x: self.toggle_tts())
        # self.root.after(500, self.start_threads)

        threading.Thread(target=self.ui_update_thread).start()

        self.root.mainloop()
        self.root.destroy()

    def transcription_callback(self, msg: TranscriptionMsg):
        if not msg.text:
            return
        translated = self.sub_translation(msg.text)[0]["translation_text"]
        # translated = msg.text
        self.add_subtitles(f"{msg.speaker}: {translated}")

        if msg.channel == OutputChannel.TTS:
            self.tts_q.put(
                TTSMsg(
                    text=msg.text,
                )
            )

    def ui_update_thread(self):
        msg: UIStateUpdateMsg
        for msg in iter(self.ui_udate_q.get, None):
            if msg.add_transcription is not None:
                self.transcription_callback(msg.add_transcription)
            if msg.set_recording_state is not None:
                self.set_recording_status(msg.set_recording_state)
            if msg.set_tts_status is not None:
                if msg.set_tts_status:
                    self.tts_label["text"] = 'tts'
                    self.args.is_tts_mode.set()
                else:
                    self.tts_label["text"] = 'sub'
                    self.args.is_tts_mode.clear()
