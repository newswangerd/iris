import json
import os
import uuid
from datetime import datetime
from enum import Enum
from secrets import token_urlsafe
from typing import Any, Optional, Self
import wave
import numpy as np

from pydantic import BaseModel, Field, SecretStr
from pydantic.types import UUID4
from collections import OrderedDict

from iris.server import settings
from iris.server.i18n import I18NMessages

from transformers import pipeline
from transformers.models.speech_to_text.tokenization_speech_to_text import LANGUAGES


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"


class Languages(str, Enum):
    ENGLISH = "en"
    RUSSIAN = "ru"
    SPANISH = "es"


class StreamMode(str, Enum):
    CONVERSATION = "conversation"
    NORMAL = "normal"


MESSAGE_DIR = settings.data_path


def get_top_level_dirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


class User(BaseModel):
    name: str
    language: str
    role: Role
    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(token_urlsafe(32)))
    password: Optional[SecretStr] = SecretStr("")

    def json_internal(self, *args, **kwargs):
        data = self.dict()
        for k, v in data.items():
            if isinstance(v, SecretStr):
                data[k] = v.get_secret_value()
        return json.dumps(data)

    @classmethod
    def all(cls) -> list[Self]:
        users = []
        for dir in get_top_level_dirs(os.path.join(MESSAGE_DIR, "users")):
            users.append(cls.load_from_file(dir))
        return users

    @classmethod
    def load_from_file(cls, name):
        path = os.path.join(MESSAGE_DIR, "users", name, "user_data.json")
        return cls.parse_file(path)

    def save_to_file(self):
        path = os.path.join(MESSAGE_DIR, "users", self.name, "user_data.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(self.json_internal())


class Message(BaseModel):
    text: str
    user: str
    language: str
    translated_text: dict[str, str] = {}
    original_text: Optional[str] = None
    is_accepted: Optional[bool] = None
    re_recording: Optional[UUID4] = None
    id: UUID4 = Field(default_factory=lambda: uuid.uuid4())
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    is_conversation_mode: bool = False

    @classmethod
    def load_from_file(cls, user, id):
        path = os.path.join(MESSAGE_DIR, "users", user, str(id) + ".json")
        return cls.parse_file(path)

    def save_to_file(self):
        path = os.path.join(MESSAGE_DIR, "users", self.user, str(self.id) + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(self.json())

    def save_audio(self, audio):
        path = os.path.join(MESSAGE_DIR, "users", self.user, str(self.id) + ".wav")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with wave.open(path, "w") as wav_file:
            # Define audio parameters
            audio = np.int16(audio * 32767)
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # Two bytes per sample
            wav_file.setframerate(16000)

            # Convert the NumPy array to bytes and write it to the WAV file
            wav_file.writeframes(audio.tobytes())

    def save_to_log(self):
        path = os.path.join(
            MESSAGE_DIR, "log", datetime.now().strftime("%Y-%m-%d") + ".txt"
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write("\n" + self.json())

    @classmethod
    def get_last_messages(cls, num_items: int) -> list[Self]:
        path = os.path.join(
            MESSAGE_DIR, "log", datetime.now().strftime("%Y-%m-%d") + ".txt"
        )
        lines = []

        try:
            with open(path, "r") as f:
                lines = f.read().strip("\n").split("\n")
        except:
            return []

        if len(lines) >= num_items:
            export_slice = lines
        else:
            export_slice = lines[num_items * -1 :]

        messages = []
        for msg in export_slice:
            if msg:
                messages.append(cls.model_validate_json(msg))

        return messages

    @staticmethod
    def clear_last_messages():
        path = os.path.join(
            MESSAGE_DIR, "log", datetime.now().strftime("%Y-%m-%d") + ".txt"
        )
        try:
            os.remove(path)
        except FileNotFoundError:
            return


class CorrectedMessage(BaseModel):
    corrected_text: str


class TokenResp(BaseModel):
    auth_code: str


class StreamMessage(BaseModel):
    re_recording: Optional[UUID4] = None
    mode: Optional[StreamMode] = StreamMode.NORMAL


class TranscriptionMessage(BaseModel):
    audio: Any
    user: User
    recording_meta: Optional[StreamMessage]


class I18NConfig(BaseModel):
    language: Languages
    messages: OrderedDict
    last_update_hash: str

    @classmethod
    def load_language(cls, language):
        path = os.path.join(MESSAGE_DIR, "i18n", language + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)

        try:
            data = cls.parse_file(path)
            if data.last_update_hash != I18NMessages.get_hash():
                return cls.init_lang(language)
            else:
                return data
        except:
            return cls.init_lang(language)

    @classmethod
    def init_lang(cls, language):
        message_dict = OrderedDict()
        if language != Languages.ENGLISH:
            translation_model = pipeline(
                "translation",
                model=f"Helsinki-NLP/opus-mt-en-{language}",
                device=settings.device,
            )

            for k in I18NMessages.messages:
                out = translation_model(k)
                message_dict[k] = " ".join([m["translation_text"] for m in out])
        else:
            for k in I18NMessages.messages:
                message_dict[k] = k

        messages = cls(
            language=language,
            last_update_hash=I18NMessages.get_hash(),
            messages=message_dict,
        )
        messages.save_to_file()
        return messages

    def save_to_file(self):
        path = os.path.join(MESSAGE_DIR, "i18n", self.language + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w") as f:
            f.write(self.json())
