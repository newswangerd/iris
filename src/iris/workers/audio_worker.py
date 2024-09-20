import logging
import traceback
from collections import deque

import numpy as np
import pyaudio
import torch

from iris.data_types import (OutputChannel, ProcessArgs, RecorderState,
                             VoiceChunkMsg)
from iris.workers.base_worker import IRISWorker

CHUNK_SECONDS = 5


class AudioWorker(IRISWorker):
    def __init__(self, audio_out_q, args: ProcessArgs):
        # self.audio_queue = audio_queue

        # For some reason this has to come before the audio is initialized
        self.model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad"
        )

        self.args = args
        self.audio_interface = pyaudio.PyAudio()

        if self.args.settings.input_device_index is None:
            default_device = self.audio_interface.get_default_input_device_info()
            input_device_index = default_device["index"]
        self.stream = self.audio_interface.open(
            rate=self.args.settings.sample_rate,
            format=pyaudio.paInt16,
            channels=1,
            input=True,
            frames_per_buffer=self.args.settings.buffer_size,
            input_device_index=self.args.settings.input_device_index,
        )

        self.audio_out_q = audio_out_q

        self.frames_per_second = int(
            args.settings.sample_rate / args.settings.buffer_size
        )

        self.recording = False
        self.vad_countdown = 0
        self.buffer = []
        self.first_pause = True
        self.counter = 0
        self.rolling_buffer = deque(maxlen=int(self.frames_per_second / 2))

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

        self.args.ui_update_q.put(
            {"set_recording_state": {"state": RecorderState.LISTENING}}
        )

        self.counter += 1

    def vad(self, aud):
        if self.args.pause_recording_event.is_set():
            if self.first_pause:
                self.args.ui_update_q.put(
                    {"set_recording_state": {"state": RecorderState.OFFLINE}}
                )
            first_pause = False
            if len(self.buffer) > 0:
                self.buffer = []
            return
        elif self.first_pause is False:
            self.args.ui_update_q.put(
                {"set_recording_state": {"state": RecorderState.LISTENING}}
            )

        first_pause = True

        vad = self.model(torch.from_numpy(self.process_stream(aud)), 16000).item()

        if (
            vad >= self.args.settings.silero_threshold and not self.recording
        ) or vad >= 0.8:
            over_time = len(self.buffer) / self.frames_per_second
            if over_time >= CHUNK_SECONDS + 1 and not self.args.is_tts_mode.is_set():
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
                    b"".join(list(self.rolling_buffer) + self.buffer), dtype=np.int16
                )
            )
            self.send_audio(audio)
            self.buffer.clear()
            self.rolling_buffer.clear()
        else:
            self.rolling_buffer.append(aud)

    def _run(self) -> None:
        try:
            while not self.args.shutdown_event.is_set():
                try:
                    data = self.stream.read(self.args.settings.buffer_size)

                except OSError as e:
                    if e.errno == pyaudio.paInputOverflowed:
                        logging.warning("Input overflowed. Frame dropped.")
                    else:
                        logging.error(f"Error during recording: {e}")
                    tb_str = traceback.format_exc()
                    print(f"Traceback: {tb_str}")
                    print(f"Error: {e}")
                    continue

                except Exception as e:
                    logging.error(f"Error during recording: {e}")
                    tb_str = traceback.format_exc()
                    print(f"Traceback: {tb_str}")
                    print(f"Error: {e}")
                    continue

                self.vad(data)

        except KeyboardInterrupt:
            logging.debug(
                "Audio data worker process " "finished due to KeyboardInterrupt"
            )
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.audio_interface.terminate()
