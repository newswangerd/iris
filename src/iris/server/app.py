import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from iris.server.api import api, auth_codes
from iris.server.auth import create_token
from iris.server.models import Message, User

app = FastAPI()


class BasicAuth(BaseModel):
    username: str
    password: str


class AuthCode(BaseModel):
    auth_code: str


@app.post("/auth/login")
async def login_basic(response: Response, credentials: BasicAuth):
    print(credentials)
    u = User.load_from_file(credentials.username)
    if u.password.get_secret_value() == credentials.password:
        response.set_cookie(key="session_token", value=create_token(u))
    else:
        raise HTTPException(status_code=401)


@app.post("/auth/auth-code")
async def login_auth_code(response: Response, credentials: AuthCode):
    if credentials.auth_code not in auth_codes:
        raise HTTPException(status_code=401)

    u = User.load_from_file(auth_codes.pop(credentials.auth_code))
    print(u)
    response.set_cookie(key="session_token", value=create_token(u))


@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("session_token")


app.mount(
    "/api",
    api,
)
app.mount(
    "/",
    StaticFiles(directory="/Users/david/code/iris/my-app/build", html=True),
    name="static",
)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        # ssl_keyfile="/Users/david/code/iris/key.pem",
        # ssl_certfile="/Users/david/code/iris/cert.pem",
    )
