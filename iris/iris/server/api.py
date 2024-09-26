import secrets
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, WebSocket
from pydantic.types import UUID4

from iris.server import translated_broker, whisper_out_q
from iris.server.auth import get_current_user, is_admin
from iris.server.models import CorrectedMessage, Message, TokenResp, User
from iris.server.websocket_stream import receive_stream

api = FastAPI(dependencies=[Depends(get_current_user)])
auth_codes: dict[str, str] = {}


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

    whisper_out_q.put(m)

    m.save_to_file()


@api.post("/messages/{user}/reject/{id}")
async def reject_message(id: UUID4, user: str):
    m = Message.load_from_file(user, id)
    m.is_accepted = False
    m.save_to_file()


@api.get("/users", dependencies=[Depends(is_admin)])
async def user_list() -> list[User]:
    return User.all()


@api.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@api.post("/users", dependencies=[Depends(is_admin)])
async def user_create(user: User) -> User:
    user.save_to_file()
    return user


@api.get("/users/{name}", dependencies=[Depends(is_admin)])
async def user_detail(name: str) -> User:
    return User.load_from_file(name)


@api.post("/users/{name}/auth-code", dependencies=[Depends(is_admin)])
async def user_create_token(name: str) -> TokenResp:
    u = User.load_from_file(name)
    code = secrets.token_urlsafe(32)
    auth_codes[code] = u.name
    return TokenResp(auth_code=code)


@api.get("/recent-messages")
async def get_recent_messages() -> list[Message]:
    return Message.get_last_messages(10)[::-1]


@api.websocket("/ws-whisper")
async def whisper(websocket: WebSocket, current_user: User = Depends(get_current_user)):
    await websocket.accept()
    id = translated_broker.register(websocket)
    try:
        await receive_stream(websocket, current_user)
    # to handle the RuntimeError: Cannot call "receive" once a disconnect message has been received. error
    except RuntimeError:
        pass
    finally:
        translated_broker.remove(id)
