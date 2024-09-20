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
from iris.server.models import Message, User
from iris.server.transcription import Transcribulator

transcribulator = Transcribulator()


# This is kind of an abomination, but I don't know what else to do. If the websocket isn't
# running on the same process (or maybe even the same thread) as the instance of this class,
# it will absolutely break.
class PubSub:
    def __init__(self):
        self.sockets: dict[str, WebSocket] = {}

    def register(self, socket):
        id = str(uuid4())
        self.sockets[id] = socket
        return id

    def remove(self, id):
        if id in self.sockets:
            del self.sockets[id]

    async def send(self, data):
        to_del = []
        for k, sock in self.sockets.items():
            try:
                await sock.send_text(data)
            except:
                print("Removing socket ", k)
                to_del.append(k)
        for k in to_del:
            del self.sockets[k]


translated_pub_sub = PubSub()


class CorrectedMessage(BaseModel):
    corrected_text: str


class TokenResp(BaseModel):
    auth_code: str


api = FastAPI(dependencies=[Depends(get_current_user)])
auth_codes: dict[str, str] = {}


@api.post("/messages/{user}/accept/{id}")
async def accept_message(
    id: UUID4, user: str, update_text: Optional[CorrectedMessage] = None
):
    m = Message.load_from_file(user, id)

    if update_text:
        m.corrected_text = update_text.corrected_text
        to_trans = m.corrected_text
    else:
        to_trans = m.text

    # if m.language != settings.USER_LANG:
    print("adding translation")
    m.translated_text = await asyncio.to_thread(transcribulator.translate, to_trans)

    m.is_accepted = True
    m.save_to_file()
    await translated_pub_sub.send(m.json())


@api.post("/messages/{user}/reject/{id}")
async def reject_message(id: UUID4, user: str):
    m = Message.load_from_file(user, id)
    m.is_accepted = False
    m.save_to_file()


@api.put("/messages/{id}")
async def update_message(message: Message, id: UUID4):
    message.save_to_file()


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


@api.websocket("/ws-whisper")
async def whisper(websocket: WebSocket, current_user: User = Depends(get_current_user)):
    await websocket.accept()

    is_streaming = False
    buffer = deque()

    while True:
        try:
            data = await websocket.receive()
            if "text" in data:
                if data["text"] == "START":
                    print("start stream")
                    buffer.clear()
                    is_streaming = True
                elif data["text"] == "STOP":
                    if len(buffer) == 0:
                        continue
                    print("end stream")

                    message = await asyncio.to_thread(
                        transcribulator.transcribe, buffer, current_user
                    )
                    if message:
                        await websocket.send_text(message.json())
                    else:
                        await websocket.send_json({})

                    is_streaming = False
            elif is_streaming:
                buffer.append(data["bytes"])
        except:
            break


@api.websocket("/ws-translation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    id = translated_pub_sub.register(websocket)
    while True:
        try:
            data = await websocket.receive()
        except Exception as e:
            translated_pub_sub.remove(id)
            break
