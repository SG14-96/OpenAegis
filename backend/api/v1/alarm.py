from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from alarm.manager import AlarmManager
from alarm.ws_manager import WSManager
from alarm.state import AlarmState
from dependencies import get_current_user

router = APIRouter()


def _manager(ws: WebSocket) -> AlarmManager:
    return ws.app.state.alarm_manager


# ------------------------------------------------------------------ #
#  HTTP endpoints                                                      #
# ------------------------------------------------------------------ #

from fastapi import Request


def _get_manager(request: Request) -> AlarmManager:
    return request.app.state.alarm_manager


def _get_state(request: Request) -> AlarmState:
    return request.app.state.alarm_state


@router.get("/state")
async def get_state(state: AlarmState = Depends(_get_state), _=Depends(get_current_user)):
    return state.model_dump()


@router.get("/plugins")
async def list_plugins(manager: AlarmManager = Depends(_get_manager), _=Depends(get_current_user)):
    return {"plugins": manager.loaded_plugins}


@router.post("/command/{plugin_name}")
async def send_command(
    plugin_name: str,
    message: dict,
    manager: AlarmManager = Depends(_get_manager),
    _=Depends(get_current_user),
):
    try:
        manager.send_to_plugin(plugin_name, message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "sent"}


# ------------------------------------------------------------------ #
#  WebSocket endpoint                                                  #
# ------------------------------------------------------------------ #

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    ws_manager: WSManager = ws.app.state.ws_manager
    alarm_state: AlarmState = ws.app.state.alarm_state
    alarm_manager: AlarmManager = ws.app.state.alarm_manager

    await ws_manager.connect(ws)
    try:
        # Push current state immediately on connect so the client is in sync.
        await ws.send_text(alarm_state.model_dump_json())

        while True:
            # Clients can send commands: {"plugin": "<name>", "type": "<cmd>", ...}
            data: dict = await ws.receive_json()
            plugin_name = data.get("plugin")
            if plugin_name:
                try:
                    alarm_manager.send_to_plugin(plugin_name, data)
                except KeyError as exc:
                    await ws.send_text(f'{{"error": "{exc}"}}')
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
