import faster_whisper
import time
import logging
from typing import Optional

from iris.data_types import (
    TranscriptionMsg,
    VoiceChunkMsg,
    ProcessArgs,
    OutputChannel,
    UIStateUpdateMsg,
)
from iris.workers.base_worker import IRISWorker
import torch.multiprocessing as mp


class WhisperWorker(IRISWorker):
    def __init__(self, audio_q: mp.Queue, args: ProcessArgs):
        self.audio_q = audio_q
        self.args = args
        self.model = faster_whisper.WhisperModel(
            model_size_or_path=self.args.settings.model_path,
            device=self.args.settings.device,
            compute_type=self.args.settings.compute_type,
            device_index=self.args.settings.gpu_device_index,
            num_workers=2,
        )

    def _run(self) -> None:
        msg: VoiceChunkMsg
        for msg in iter(self.audio_q.get, None):
            segments, info = self.model.transcribe(
                msg.audio,
                language=msg.msg_lang,
                beam_size=self.args.settings.beam_size,
                initial_prompt=self.args.settings.initial_prompt,
                suppress_tokens=self.args.settings.suppress_tokens,
                word_timestamps=True,
                clip_timestamps=msg.timestamps,
                # repetition_penalty=0,
            )

            transcription = " ".join(seg.text for seg in segments)
            transcription = transcription.strip()
            self.args.ui_update_q.put(
                UIStateUpdateMsg(
                    add_transcription=TranscriptionMsg(
                        msg_lang=msg.msg_lang,
                        target_lang=msg.target_lang,
                        speaker=msg.speaker,
                        time_start=msg.time_start,
                        text=transcription,
                        channel=msg.channel,
                    )
                )
            )
