from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Sub-app is starting up")
    yield
    print("Sub-app is shutting down")

sub_app = FastAPI(lifespan=lifespan)

@sub_app.get("/sub")
async def sub_root():
    return {"message": "Hello from sub-app"}

main_app = FastAPI()

main_app.mount("/subapp", sub_app)

@main_app.get("/")
async def main_root():
    return {"message": "Hello from main app"}
