import asyncio
import concurrent.futures
import io

import faster_whisper
import numpy as np
from pydub import AudioSegment
from transformers import pipeline

from iris.server.models import Message, User


class Transcribulator:
    def __init__(self):

        self.user_lang_translation = pipeline(
            "translation",
            model=f"Helsinki-NLP/opus-mt-es-en",
            device="cpu",
        )

        self.whisper = faster_whisper.WhisperModel(
            model_size_or_path="tiny",
            device="cpu",
            # compute_type="default",
            # device_index=0,
            # num_workers=4,
        )

    def translate(self, text: str) -> str:
        return self.user_lang_translation(text)[0]["translation_text"]

    def process_stream(self, buffer):
        audio_io = io.BytesIO(b"".join(buffer))
        a = AudioSegment.from_file(audio_io)
        return a.set_frame_rate(16000)

        # I don't know why, but this was working and then mystiously stopped. I think this was a little
        # bit faster, so I'm going to leave it here in case I want to come back and fixe it later
        # audio_int16 = np.frombuffer(a.raw_data, np.int16)
        # abs_max = np.abs(audio_int16).max()
        # print(f"Absolute max value: {abs_max}")
        # sound = audio_int16.astype(np.float32)
        # if abs_max > 0:
        #     sound *= 1 / 32768.0
        # print(f"Float32 array shape: {sound.shape}, dtype: {sound.dtype}")
        # print(f"Float32 array min: {sound.min()}, max: {sound.max()}")
        # sound = sound.squeeze()  # depends on the use case

        # return sound, a

    def transcribe(self, buffer, user: User):
        audio_segment = self.process_stream(buffer)
        f = io.BytesIO()

        print(user)

        audio_segment.export(f, format="wav")
        segments, info = self.whisper.transcribe(
            f,
            language=user.language,
            beam_size=5,
            # initial_prompt=None,
            # suppress_tokens=[-1],
            # word_timestamps=True,
            # clip_timestamps=[0],
        )

        print(info)

        transcription = " ".join(seg.text for seg in segments)
        transcription = transcription.strip()

        if not transcription:
            return None

        m = Message(text=transcription, user=user.name, language=user.language)
        m.save_to_file()
        m.save_audio(audio_segment)
        return m
