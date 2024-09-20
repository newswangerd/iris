import os
import time
from collections import deque

import numpy as np
import torch
import torch.multiprocessing as mp
import torchaudio
from pyannote.audio import Pipeline as PyAnnotePipeline
from pyannote.audio.core.model import Output
from scipy.io.wavfile import write
from torchaudio.io import StreamReader

from iris.data_types import OutputChannel, ProcessArgs, RecorderState, VoiceChunkMsg
from iris.workers.base_worker import IRISWorker

CHUNK_SECONDS = 5


class DiarizationProcessor:
    def __init__(self, settings, send_audio):
        token = os.environ.get("IRIS_HUGGING_FACE_TOKEN", None)
        self.pyannote = PyAnnotePipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token,
        )

        self.settings = settings
        self.send_audio = send_audio

    def send_diarized(self, audio):
        last_speaker = None
        """
        timestamps = [
            (speaker, (start, end))
        ]
        """
        timestamps = []
        diarization = self.pyannote(
            {
                "waveform": torch.from_numpy(audio).unsqueeze(0),
                "sample_rate": self.settings.sample_rate,
            }
        )
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if speaker == last_speaker:
                timestamps[-1][1][1] = turn.end
            else:
                if len(timestamps) > 0:
                    start = timestamps[-1][1][1]
                else:
                    start = 0

                if turn.end - start < 0.5:
                    continue

                timestamps.append((speaker, [start, turn.end]))

            last_speaker = speaker

        if timestamps:
            timestamps[-1][1].pop()

        for speaker, times in timestamps:
            self.send_audio(audio, speaker=speaker, timestamps=times)


class VADWorker(IRISWorker):
    def __init__(
        self,
        audio_in_q: mp.Queue,
        audio_out_q: mp.Queue,
        args: ProcessArgs,
    ):
        self.audio_in_q = audio_in_q
        self.audio_out_q = audio_out_q
        self.args = args

        self.frames_per_second = int(
            args.settings.sample_rate / args.settings.buffer_size
        )
        self.dp = DiarizationProcessor(args.settings, self.send_audio)

        self.model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad"
        )

        self.recording = False
        self.vad_countdown = 0
        self.buffer = []

    def process_stream(self, sound):
        audio_int16 = np.frombuffer(sound, np.int16)
        abs_max = np.abs(audio_int16).max()
        sound = audio_int16.astype(np.float32)
        if abs_max > 0:
            sound *= 1 / 32768
        sound = sound.squeeze()  # depends on the use case
        return sound

    def send_audio(self, audio, speaker=None, timestamps=[0]):
        is_tts = self.args.is_tts_mode.is_set()

        if is_tts:
            self.args.pause_recording_event.set()

        self.audio_out_q.put(
            VoiceChunkMsg(
                audio=audio,
                msg_lang=(
                    self.args.settings.user_lang
                    if is_tts
                    else self.args.settings.external_lang
                ),
                target_lang=(
                    self.args.settings.external_lang
                    if is_tts
                    else self.args.settings.user_lang
                ),
                channel=OutputChannel.TTS if is_tts else OutputChannel.SUB,
                speaker=speaker,
                timestamps=timestamps,
                count=self.counter,
            )
        )

        print(f"Sent message {self.counter}")

        self.counter += 1

    def _run(self) -> None:
        self.args.ui_update_q.put(
            {"set_recording_state": {"state": RecorderState.LISTENING}}
        )
        self.buffer = []
        rolling_buffer = deque(maxlen=int(self.frames_per_second / 2))
        first_pause = True
        self.counter = 0
        for aud in iter(self.audio_in_q.get, None):
            if self.args.pause_recording_event.is_set():
                if first_pause:
                    self.args.ui_update_q.put(
                        {"set_recording_state": {"state": RecorderState.OFFLINE}}
                    )
                first_pause = False
                if len(self.buffer) > 0:
                    self.buffer = []
                continue
            elif first_pause is False:
                self.args.ui_update_q.put(
                    {"set_recording_state": {"state": RecorderState.LISTENING}}
                )

            first_pause = True

            vad = self.model(torch.from_numpy(self.process_stream(aud)), 16000).item()

            if (
                vad >= self.args.settings.silero_threshold and not self.recording
            ) or vad >= 0.9:
                over_time = len(self.buffer) / self.frames_per_second
                if (
                    over_time >= CHUNK_SECONDS + 1
                    and not self.args.is_tts_mode.is_set()
                ):
                    diff = over_time - CHUNK_SECONDS
                    self.vad_countdown = int(self.frames_per_second * (1 / diff))
                else:
                    self.vad_countdown = self.frames_per_second
                if not self.recording:
                    self.args.ui_update_q.put(
                        {"set_recording_state": {"state": RecorderState.RECORDING}}
                    )
                self.recording = True

            if self.vad_countdown > 0:
                self.vad_countdown -= 1
            else:
                if self.recording:
                    self.args.ui_update_q.put(
                        {"set_recording_state": {"state": RecorderState.LISTENING}}
                    )

                self.recording = False

            if self.recording:
                self.buffer.append(aud)

            elif len(self.buffer) != 0:
                audio = self.process_stream(
                    np.frombuffer(
                        b"".join(list(rolling_buffer) + self.buffer), dtype=np.int16
                    )
                )
                self.dp.send_diarized(audio)
                # self.send_audio(audio)
                self.buffer.clear()
                rolling_buffer.clear()
            else:
                rolling_buffer.append(aud)
