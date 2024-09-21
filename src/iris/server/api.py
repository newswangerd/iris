import asyncio
import secrets
from collections import deque
from typing import Annotated, Optional
from uuid import uuid4

import jwt
from fastapi import BackgroundTasks, Depends, FastAPI, WebSocket
from pydantic import BaseModel
from pydantic.types import UUID4

from iris.server import settings
from iris.server.auth import create_token, get_current_user
from iris.server.models import Languages, Message, User
from iris.server.transcription import Transcribulator

transcribulator = Transcribulator()


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


class CorrectedMessage(BaseModel):
    corrected_text: str


class TokenResp(BaseModel):
    auth_code: str


api = FastAPI(dependencies=[Depends(get_current_user)])
auth_codes: dict[str, str] = {}


async def translate_and_send(m: Message):
    print("adding translation")
    if m.language == settings.base_language:
        for lang in settings.supported_languages:
            m.translated_text[lang] = transcribulator.translate(
                m.text, (m.language, lang)
            )
    else:
        m.translated_text[settings.base_language] = transcribulator.translate(
            m.text,
            (m.language, settings.base_language),
        )

    await translated_broker.send(m.json())
    m.save_to_file()
    m.save_to_log()


@api.post("/messages/{user}/accept/{id}")
async def accept_message(
    id: UUID4,
    user: str,
    background_tasks: BackgroundTasks,
    update_text: Optional[CorrectedMessage] = None,
):
    m = Message.load_from_file(user, id)

    if m.is_accepted:
        return

    m.is_accepted = True

    if update_text:
        m.original_text = m.text
        m.text = update_text.corrected_text

    background_tasks.add_task(translate_and_send, m)

    m.save_to_file()


@api.post("/messages/{user}/reject/{id}")
async def reject_message(id: UUID4, user: str):
    m = Message.load_from_file(user, id)
    m.is_accepted = False
    m.save_to_file()


@api.get("/users")
async def user_list() -> list[User]:
    return User.all()


@api.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@api.post("/users")
async def user_create(user: User) -> User:
    user.save_to_file()
    return user


@api.get("/users/{name}")
async def user_detail(name: str) -> User:
    return User.load_from_file(name)


@api.post("/users/{name}/auth-code")
async def user_create_token(name: str) -> TokenResp:
    u = User.load_from_file(name)
    code = secrets.token_urlsafe(32)
    auth_codes[code] = u.name
    return TokenResp(auth_code=code)


@api.get("/recent-messages")
async def get_recent_messages() -> list[Message]:
    return Message.get_last_messages(10)


@api.websocket("/ws-whisper")
async def whisper(websocket: WebSocket, current_user: User = Depends(get_current_user)):
    await websocket.accept()

    is_streaming = False
    buffer = deque()
    recording_meta = None
    id = translated_broker.register(websocket)

    while True:
        try:
            data = await websocket.receive()
            if "text" in data:
                if data["text"].startswith("START:"):
                    _, recording_meta = data["text"].split(":", maxsplit=1)

                    print("start stream")
                    buffer.clear()
                    is_streaming = True
                elif data["text"] == "STOP":

                    if len(buffer) == 0:
                        continue
                    print("end stream")

                    message = await asyncio.to_thread(
                        transcribulator.transcribe, buffer, current_user, recording_meta
                    )
                    recording_meta = None
                    if message:
                        await websocket.send_text(message.json())
                    else:
                        await websocket.send_json({})

                    is_streaming = False
            elif is_streaming:
                buffer.append(data["bytes"])
        except:
            translated_broker.remove(id)
            break
