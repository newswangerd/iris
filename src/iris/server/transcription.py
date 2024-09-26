import faster_whisper
from transformers import pipeline

from iris.server import settings
from iris.server.models import Message, StreamMode, TranscriptionMessage


class Translator:
    def __init__(self):
        self.translation_models = {}

        # TODO: might be worthwhile to use the helsinki multi language models for english.
        for lang in settings.supported_languages:
            if lang == settings.base_language:
                continue
            self.translation_models[(settings.base_language, lang)] = pipeline(
                "translation",
                model=f"Helsinki-NLP/opus-mt-{settings.base_language}-{lang}",
                device="cpu",
            )

            self.translation_models[(lang, settings.base_language)] = pipeline(
                "translation",
                model=f"Helsinki-NLP/opus-mt-{lang}-{settings.base_language}",
                device="cpu",
            )

    def translate(self, text: str, lang_key: tuple[str, str]) -> str:
        out = self.translation_models[lang_key](text)
        return " ".join([m["translation_text"] for m in out])


class Transcriber:
    def __init__(self):
        self.whisper = faster_whisper.WhisperModel(
            # model_size_or_path="distil-large-v3",
            model_size_or_path=settings.whisper_model,
            device="cpu",
            cpu_threads=4,
            num_workers=2,
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
        # m.save_audio(audio_segment)
        return m
