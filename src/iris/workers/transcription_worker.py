import logging
import time
from typing import Optional

import faster_whisper
import torch.multiprocessing as mp

from iris.data_types import OutputChannel, ProcessArgs, TranscriptionMsg, VoiceChunkMsg
from iris.workers.base_worker import IRISWorker


class WhisperWorker(IRISWorker):
    def __init__(self, audio_q: mp.Queue, args: ProcessArgs):
        self.audio_q = audio_q
        self.args = args
        self.model = faster_whisper.WhisperModel(
            model_size_or_path=self.args.settings.model_path,
            device=self.args.settings.whisper_device,
            compute_type=self.args.settings.compute_type,
            device_index=self.args.settings.gpu_device_index,
            num_workers=4,
        )

    def _run(self) -> None:
        msg: VoiceChunkMsg
        for msg in iter(self.audio_q.get, None):
            print(f"received message {msg.count}")
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
                {
                    "add_transcription": {
                        "msg": TranscriptionMsg(
                            msg_lang=msg.msg_lang,
                            target_lang=msg.target_lang,
                            speaker=msg.speaker,
                            time_start=msg.time_start,
                            text=transcription,
                            channel=msg.channel,
                        )
                    }
                }
            )
