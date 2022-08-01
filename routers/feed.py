import pathlib

from typing import List
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Depends,
    HTTPException,
    Cookie,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import auth
from utils.users_utils import get_current_user, get_user
from utils.token_utils import decode_access_token, oauth2_scheme

router = APIRouter()


BASE_DIR = pathlib.Path(__file__).parent.parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Taken from FastAPI Documentation: https://fastapi.tiangolo.com/advanced/websockets/
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


socket_manager = ConnectionManager()


@router.get("/feed", response_class=HTMLResponse)
async def read_feed(request: Request, token: str = Cookie(None)):
    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

    user = decode_access_token(token)
    return templates.TemplateResponse(
        "chat.html", {"request": request, "username": user.username}
    )


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await socket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await socket_manager.send_personal_message(f"You wrote: {data}", websocket)
            await socket_manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)
        await socket_manager.broadcast(f"Client #{client_id} left the chat")
