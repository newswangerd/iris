from uuid import uuid4
import os
from fastapi import WebSocket
from pydantic import BaseModel
from torch import multiprocessing as mp
from typing import Optional


class Settings(BaseModel):
    # TODO remove these temporary values
    data_path: str = "./dev/web_messages/"
    base_language: str = "en"
    supported_languages: list[str] = [
        # "ru",
        "es",
    ]
    static_root: str = "./ui/build"
    whisper_model: str = "base"
    ssl_keyfile: Optional [str] = "./dev/certs/key.pem"
    ssl_certfile: Optional [str] = "./dev/certs/cert.pem"
    device: str = "cpu"
    auto_code_reload: bool = True
    http_port: int = 8000

    @classmethod
    def load(cls):
        """
        Loop through env vars that match the settings
        """
        kwargs = {}
        for field in cls.model_fields:
            if val := os.environ.get("IRIS_" + field.upper()):
                if val == "NONE":
                    val = None
                elif val == "FALSE":
                    val = False
                elif val == "TRUE":
                    val = True
                kwargs[field] = val

        return cls(**kwargs)


# This is kind of an abomination, but I don't know what else to do. If the websocket isn't
# running on the same process (or maybe even the same thread) as the instance of this class,
# it will absolutely break.
class MessageBroker:
    def __init__(self):
        self.sockets: dict[str, WebSocket] = {}

    def register(self, socket):
        id = str(uuid4())
        self.sockets[id] = socket
        return id

    def remove(self, id):
        if id in self.sockets:
            del self.sockets[id]

    async def reap(
        self,
    ):
        # TODO: loop through the current sockets and remove any closed ones
        pass

    async def send(self, data):
        # TODO: do this with asyncio.gather
        to_del = []
        for k, sock in self.sockets.items():
            try:
                await sock.send_text(data)
            except:
                print("Removing socket ", k)
                to_del.append(k)
        for k in to_del:
            self.remove(k)


translated_broker = MessageBroker()
audio_in_q = mp.Queue()
whisper_out_q = mp.Queue()
settings = Settings.load()
