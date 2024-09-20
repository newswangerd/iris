import json
import os
import uuid
from datetime import datetime
from enum import Enum
from secrets import token_urlsafe
from typing import Optional, Self

from pydantic import BaseModel, Field, SecretStr, field_serializer
from pydantic.json_schema import SkipJsonSchema
from pydantic.types import UUID4

from iris.server import settings


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"


class Languages(str, Enum):
    ENGLISH = "en"
    RUSSIAN = "ru"
    SPANISH = "es"


MESSAGE_DIR = settings.data_path


def get_top_level_dirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


class User(BaseModel):
    name: str
    language: str
    role: Role
    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(token_urlsafe(32)))
    password: Optional[SecretStr] = SecretStr(token_urlsafe(32))

    # @field_serializer("password", "secret_key", when_used="json")
    # def dump_secret(self, v):
    #     return v.get_secret_value()

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

    @classmethod
    def load_from_file(cls, user, id):
        path = os.path.join(MESSAGE_DIR, "users", user, str(id) + ".json")
        return cls.parse_file(path)

    def save_to_file(self):
        path = os.path.join(MESSAGE_DIR, "users", self.user, str(self.id) + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(self.json())

    def save_audio(self, audio_segment):
        path = os.path.join(MESSAGE_DIR, "users", self.user, str(self.id) + ".wav")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        audio_segment.export(path, format="wav")
