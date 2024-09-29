import faster_whisper
from transformers import pipeline

from iris.server import settings
from iris.server.models import Message, StreamMode, TranscriptionMessage


class Translator:
    def __init__(self):
        self.model = pipe = pipeline(
            "translation",
            model="facebook/mbart-large-50-many-to-many-mmt",
            device=settings.device,
        )

    def translate(self, text: str, lang_key: tuple[str, str]) -> str:
        out = self.model(text, src_lang=lang_key[0], tgt_lang=lang_key[1])
        return " ".join([m["translation_text"] for m in out])


class Transcriber:
    def __init__(self):
        self.whisper = faster_whisper.WhisperModel(
            # model_size_or_path="distil-large-v3",
            model_size_or_path=settings.whisper_model,
            device=settings.device,
            cpu_threads=1,
            num_workers=1,
            # compute_type="default",
            # device_index=0,
            # num_workers=4,
        )

    def transcribe(self, msg: TranscriptionMessage):

        import time

        ts = time.time()

        # audio_segment.export(f, format="wav")
        segments, info = self.whisper.transcribe(
            msg.audio,
            language=msg.user.language,
            beam_size=5,
            # initial_prompt=None,
            # suppress_tokens=[-1],
            # word_timestamps=True,
            # clip_timestamps=[0],
        )

        transcription = " ".join(seg.text for seg in segments)
        transcription = transcription.strip()
        print(time.time() - ts)

        if not transcription:
            return None

        m = Message(text=transcription, user=msg.user.name, language=msg.user.language)

        if msg.recording_meta:
            print(msg.recording_meta)
            if msg.recording_meta.mode == StreamMode.CONVERSATION:
                m.is_accepted = True
                m.is_conversation_mode = True

            if msg.recording_meta.re_recording:
                m.re_recording = msg.recording_meta.re_recording

        print(m)

        m.save_to_file()
        m.save_audio(msg.audio)
        return m
