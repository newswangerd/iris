from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from torch import multiprocessing as mp
from datetime import datetime, timedelta, timezone

from iris.server import audio_in_q, settings, translated_broker, whisper_out_q
from iris.server.api import api, auth_codes
from iris.server.auth import create_token
from iris.server.models import User, Languages, I18NConfig
from iris.server.workers import BrokerThread, whisper_process


@asynccontextmanager
async def lifespan(app: FastAPI):
    BrokerThread(whisper_out_q, translated_broker).start()
    mp.Process(target=whisper_process, args=[audio_in_q, whisper_out_q]).start()
    yield
    audio_in_q.put(None)
    whisper_out_q.put(None)


app = FastAPI(
    lifespan=lifespan,
)


class BasicAuth(BaseModel):
    username: str
    password: str


class AuthCode(BaseModel):
    auth_code: str


def create_session(response, user):
    return response.set_cookie(
        key="session_token",
        value=create_token(user),
        expires=datetime.now(timezone.utc) + timedelta(days=14),
    )


@app.post("/auth/login")
async def login_basic(response: Response, credentials: BasicAuth):
    u = User.load_from_file(credentials.username)
    if (
        u.password.get_secret_value() == credentials.password
        and u.password.get_secret_value() != ""
    ):
        return create_session(response, u)
    else:
        raise HTTPException(status_code=401)


@app.post("/auth/auth-code")
async def login_auth_code(response: Response, credentials: AuthCode):
    if credentials.auth_code not in auth_codes:
        raise HTTPException(status_code=401)

    u = User.load_from_file(auth_codes.pop(credentials.auth_code))
    return create_session(response, u)


@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("session_token")


@app.get("/translations/{language}")
async def get_translations(language) -> I18NConfig:
    if language in settings.supported_languages or language == settings.base_language:
        return I18NConfig.load_language(language)

    raise HTTPException(status_code=400, detail="Language not supported")


app.mount(
    "/api",
    api,
)
app.mount(
    "/",
    StaticFiles(directory=settings.static_root, html=True),
    name="static",
)

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.http_port,
        ssl_keyfile=settings.ssl_keyfile,
        ssl_certfile=settings.ssl_certfile,
        reload=settings.auto_code_reload,
    )
