from collections import deque
from typing import Callable, Optional

import numpy as np
import torch

CHUNK_SECONDS = 3


# TODO: I want to refactor audio worker to user this class


class VADHandler:
    def __init__(
        self,
        vad_threshold=0.6,
        on_recording_state_change: Optional[
            Callable[
                [
                    bool,
                ],
                None,
            ]
        ] = None,
        on_data_ready: Optional[Callable[[np.ndarray], None]] = None,
    ):
        self.vad_threshold = vad_threshold

        self.on_recording_state_change = on_recording_state_change
        self.on_data_ready = on_data_ready

        self.model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad"
        )
        self.frames_per_second = int(1000 / 32)
        self.vad_countdown = 0
        self.buffer = []
        self.first_pause = True
        self.counter = 0
        self.rolling_buffer = deque(maxlen=int(self.frames_per_second / 2))
        self.recording = False

    def process_stream(self, sound):
        audio_int16 = np.frombuffer(sound, np.int16)
        abs_max = np.abs(audio_int16).max()
        sound = audio_int16.astype(np.float32)
        if abs_max > 0:
            sound *= 1 / 32768
        sound = sound.squeeze()  # depends on the use case
        return sound

    def send_audio(self):
        print("sending audio")
        if self.on_data_ready:
            self.on_data_ready(self.get_whisper_audio())
        self.buffer.clear()
        self.rolling_buffer.clear()

    def send_recording_state(self, is_recording):
        if self.on_recording_state_change:
            self.on_recording_state_change(is_recording)

    def get_whisper_audio(self):
        return self.process_stream(
            np.frombuffer(
                b"".join(list(self.rolling_buffer) + self.buffer), dtype=np.int16
            )
        )

    def vad(self, aud, no_vad=False):
        if no_vad:
            vad = 1
        else:
            vad = self.model(torch.from_numpy(self.process_stream(aud)), 16000).item()

        if (vad >= self.vad_threshold and not self.recording) or vad >= 0.8:
            over_time = len(self.buffer) / self.frames_per_second
            if over_time >= CHUNK_SECONDS + 1:
                diff = over_time - CHUNK_SECONDS
                self.vad_countdown = int(self.frames_per_second * (1 / diff))
            else:
                self.vad_countdown = self.frames_per_second
            if not self.recording:
                self.send_recording_state(True)
            self.recording = True

        if self.vad_countdown > 0:
            self.vad_countdown -= 1
        else:
            if self.recording:
                self.send_recording_state(False)

            self.recording = False

        if self.recording:
            self.buffer.append(aud)

        elif len(self.buffer) != 0:
            self.send_audio()

        else:
            self.rolling_buffer.append(aud)
