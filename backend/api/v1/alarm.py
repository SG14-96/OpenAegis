from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from schema.settings import AlarmCreateRequestBody, AlarmUpdateRequestBody
from alarm.commands import CommandPayload
from alarm.manager import AlarmManager, PluginLoadError
from alarm.ws_manager import WSManager
from dependencies import get_current_user, get_db

router = APIRouter()


def _get_manager(request: Request) -> AlarmManager:
    return request.app.state.alarm_manager


# ------------------------------------------------------------------ #
#  Alarm creation and management                                       #
# ------------------------------------------------------------------ #
@router.get("/")
async def get_alarm_settings(
    manager: AlarmManager = Depends(_get_manager),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    from crud.settings import get_alarm_settings

    record = get_alarm_settings(db)
    if record is None:
        raise HTTPException(status_code=404, detail="No alarm configured.")

    plugin_info = None
    if record.plugin_settings_record:
        plugin_info = {
            "plugin_name": record.plugin_settings_record.plugin_name,
            "module_path": record.plugin_settings_record.data.get("module_path"),
            "setup_values": record.plugin_settings_record.data.get("setup_values"),
        }

    return {
        "alarm_name": record.alarm_name,
        "plugin": plugin_info,
        "partitions": manager.partitions,
    }

@router.post("/create", status_code=201)
async def create_alarm(
    body: AlarmCreateRequestBody,
    manager: AlarmManager = Depends(_get_manager),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    from crud.settings import get_alarm_settings, create_alarm_settings, persist_plugin_config

    if get_alarm_settings(db) is not None:
        raise HTTPException(status_code=409, detail="An alarm is already configured. Remove it before creating a new one.")

    if manager.active_plugin is not None:
        raise HTTPException(status_code=409, detail=f"Plugin '{manager.active_plugin}' is already loaded.")

    try:
        plugin_name = manager.load_plugin(body.module_path, body.setup_values)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PluginLoadError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "plugin_load_failed", "plugin": exc.plugin_name, "reason": str(exc.cause)},
        )
    except (FileNotFoundError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    plugin_settings = persist_plugin_config(db, plugin_name, body.module_path, body.setup_values)
    create_alarm_settings(db, body.alarm_name, plugin_settings)

    return {"status": "created", "alarm_name": body.alarm_name, "plugin": plugin_name}


@router.patch("/update")
async def update_alarm(
    body: AlarmUpdateRequestBody,
    manager: AlarmManager = Depends(_get_manager),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    from crud.settings import get_alarm_settings, update_alarm_settings, persist_plugin_config

    alarm = get_alarm_settings(db)
    if alarm is None:
        raise HTTPException(status_code=404, detail="No alarm configured.")

    needs_plugin_reload = body.module_path is not None or body.setup_values is not None

    if needs_plugin_reload:
        existing = alarm.plugin_settings
        old_module_path = existing.data.get("module_path") if existing else None
        old_setup_values = existing.data.get("setup_values") if existing else None

        new_module_path = body.module_path or old_module_path
        if new_module_path is None:
            raise HTTPException(
                status_code=422,
                detail="Cannot reload plugin: no module_path is set and none was provided.",
            )
        new_setup_values = body.setup_values if body.setup_values is not None else old_setup_values

        try:
            new_plugin_name = manager.reload_plugin(
                new_module_path, new_setup_values, old_module_path, old_setup_values
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except PluginLoadError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "plugin_load_failed", "plugin": exc.plugin_name, "reason": str(exc.cause)},
            )
        except (FileNotFoundError, AttributeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        persist_plugin_config(db, new_plugin_name, new_module_path, new_setup_values)

    updated = update_alarm_settings(db, body.alarm_name)
    return {"status": "updated", "alarm_name": updated.alarm_name, "plugin": manager.active_plugin}


@router.delete("/delete", status_code=200)
async def delete_alarm(
    manager: AlarmManager = Depends(_get_manager),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    from crud.settings import get_alarm_settings, delete_alarm_settings

    alarm = get_alarm_settings(db)
    if alarm is None:
        raise HTTPException(status_code=404, detail="No alarm configured.")

    if manager.active_plugin is not None:
        try:
            manager.unload_plugin()
        except Exception as exc:
            # Log but don't block deletion — DB record is removed regardless.
            import logging
            logging.getLogger(__name__).warning("Plugin unload raised during alarm deletion: %s", exc)

    delete_alarm_settings(db)
    return {"status": "deleted"}


# ------------------------------------------------------------------ #
#  Plugin info                                                         #
# ------------------------------------------------------------------ #

@router.get("/plugins/available")
async def list_available_plugins(
    manager: AlarmManager = Depends(_get_manager),
    _=Depends(get_current_user),
):
    return {"plugins": manager.list_available_plugins}

# ------------------------------------------------------------------ #
#  WebSocket                                                           #
# ------------------------------------------------------------------ #

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    ws_manager: WSManager = ws.app.state.ws_manager
    alarm_manager: AlarmManager = ws.app.state.alarm_manager

    await ws_manager.connect(ws)
    try:
        while True:
            data: dict = await ws.receive_json()
            try:
                payload = CommandPayload(**data)
            except ValidationError:
                # Not a recognized alarm command — accept it as raw client data.
                await ws.send_json({"status": "received", "data": data})
                continue

            try:
                alarm_manager.dispatch_command(payload)
            except RuntimeError as exc:
                await ws.send_json({"error": str(exc)})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
