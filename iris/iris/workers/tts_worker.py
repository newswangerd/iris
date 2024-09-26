import sounddevice
from transformers import pipeline

from iris.data_types import ProcessArgs, TTSMsg
from iris.workers.base_worker import IRISWorker

TTS_LANG_MAP = {
    "ru": "rus",
    "en": "eng",
    "es": "spa",
}


class TTSWorker(IRISWorker):
    def __init__(self, tts_in_q, args: ProcessArgs):
        self.args = args
        self.tts_in_q = tts_in_q

        if self.args.settings.external_lang in TTS_LANG_MAP:
            self.tts_pipe = pipeline(
                "text-to-speech",
                model=f"facebook/mms-tts-{TTS_LANG_MAP[self.args.settings.external_lang]}",
                device=args.settings.tts_device,
            )
            self.tts_trans_pipe = pipeline(
                "translation",
                model=f"Helsinki-NLP/opus-mt-{self.args.settings.user_lang}-{self.args.settings.external_lang}",
                device=args.settings.translation_device,
            )
        else:
            self.tts_pipe = None
            self.tts_trans_pipe = None

    def _run(self) -> None:
        if not self.tts_pipe:
            raise Exception()

        msg: TTSMsg
        for msg in iter(self.tts_in_q.get, None):
            translated = self.tts_trans_pipe(msg.text)[0]["translation_text"]
            out = self.tts_pipe(translated)
            self.args.pause_recording_event.set()
            sounddevice.play(
                out["audio"][0], samplerate=out["sampling_rate"], blocking=True
            )
            self.args.pause_recording_event.clear()
            self.args.ui_update_q.put({"set_tts_status": {"state": False}})
