from typing import Optional

import jwt
from fastapi import Depends, Cookie, HTTPException, status


from iris.server.models import User, Role


def create_token(user: User) -> str:
    return jwt.encode(
        payload={"name": user.name},
        key=user.secret_key.get_secret_value(),
        algorithm="HS256",
    )


async def get_current_user(session_token: Optional[str] = Cookie(None)) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    if not session_token:
        raise credentials_exception
    try:
        username = jwt.decode(session_token, options={"verify_signature": False}).get(
            "name"
        )
        u = User.load_from_file(username)
        jwt.decode(
            session_token, key=u.secret_key.get_secret_value(), algorithms=["HS256"]
        )
        return u
    except jwt.exceptions.PyJWTError as e:
        raise credentials_exception
    return User(username=username)


async def is_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )
