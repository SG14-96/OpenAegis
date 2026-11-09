import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from alarm.manager import AlarmManager
from api.v1 import alarm, setup
from auth import security
from dependencies import get_db
from models.models import User
from models.settings import AlarmSettings, PluginSettings
from onboarding.setup_code import MAX_FAILED_ATTEMPTS, SetupCode


class FakeWS:
    async def broadcast(self, data: str) -> None:
        pass


def _code_from_log(caplog) -> str:
    """The setup code as printed in the most recent banner (XXXX-XXXX)."""
    # The first code is logged while the `app` fixture runs, which caplog
    # files under the "setup" phase rather than the test's own records.
    records = caplog.get_records("setup") + caplog.records
    banner = [r for r in records if "setup code" in r.getMessage()][-1].getMessage()
    return next(line.strip() for line in banner.splitlines() if "-" in line and len(line.strip()) == 9)


@pytest.fixture
def app(session_factory, caplog):
    caplog.set_level(logging.WARNING, logger="onboarding.setup_code")
    app = FastAPI()
    app.include_router(setup.router, prefix="/api/v1/setup")
    app.include_router(alarm.router, prefix="/api/v1/alarm")
    app.state.alarm_manager = AlarmManager(FakeWS(), session_factory)
    app.state.setup_code = SetupCode()
    app.state.setup_code.issue()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def _admin_body(code: str, **overrides) -> dict:
    return {"setup_code": code, "username": "owner", "password": "correct-horse", **overrides}


def test_fresh_install_needs_admin(client):
    assert client.get("/api/v1/setup/status").json() == {
        "needs_admin": True,
        "has_alarm": False,
        "plugin_loaded": False,
    }


def test_first_admin_is_created_signed_in_and_only_once(client, session_factory, caplog):
    code = _code_from_log(caplog)

    res = client.post("/api/v1/setup/admin", json=_admin_body(code.lower()))  # case/dash-insensitive
    assert res.status_code == 201
    assert res.json()["access_token"] and res.json()["refresh_token"]

    with session_factory() as db:
        admin = db.query(User).one()
    assert admin.username == "owner" and admin.isSuperUser
    assert security.verify_password("correct-horse", admin.hashed_password)

    assert client.get("/api/v1/setup/status").json()["needs_admin"] is False
    # The code is spent: a second attempt can't create another admin.
    again = client.post("/api/v1/setup/admin", json=_admin_body(code, username="intruder"))
    assert again.status_code == 409


def test_wrong_code_is_rejected_and_rotates_after_repeated_misses(client, session_factory, caplog):
    first_code = _code_from_log(caplog)
    for _ in range(MAX_FAILED_ATTEMPTS):
        assert client.post("/api/v1/setup/admin", json=_admin_body("AAAA-AAAA")).status_code == 403

    # The old code no longer works; the newly logged one does.
    new_code = _code_from_log(caplog)
    assert new_code != first_code
    assert client.post("/api/v1/setup/admin", json=_admin_body(first_code)).status_code == 403
    assert client.post("/api/v1/setup/admin", json=_admin_body(new_code)).status_code == 201


def test_existing_users_block_setup_even_with_the_code(client, session_factory, caplog):
    with session_factory() as db:
        db.add(User(username="existing", hashed_password="x", isSuperUser=True))
        db.commit()

    res = client.post("/api/v1/setup/admin", json=_admin_body(_code_from_log(caplog)))
    assert res.status_code == 409


def test_short_password_is_rejected(client, caplog):
    res = client.post("/api/v1/setup/admin", json=_admin_body(_code_from_log(caplog), password="short"))
    assert res.status_code == 422


def _save_alarm(session_factory, module_path: str, setup_values: dict) -> None:
    with session_factory() as db:
        alarm_row = AlarmSettings(alarm_name="Home", data={})
        db.add(alarm_row)
        db.flush()
        db.add(PluginSettings(
            plugin_name="Saved",
            is_currently_used=True,
            data={"module_path": module_path, "setup_values": setup_values},
            alarm_settings_id=alarm_row.id,
        ))
        db.commit()


def _sign_in(client, caplog) -> dict:
    token = client.post("/api/v1/setup/admin", json=_admin_body(_code_from_log(caplog))).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_plugin_error_is_reported_only_to_signed_in_users(client, app, session_factory, caplog):
    # The DSC plugin with a port that doesn't exist fails like an unplugged panel at boot.
    _save_alarm(session_factory, "plugins.DSC.IT_100_Integration_Module", {"0": "/dev/tty.nonexistent"})
    with session_factory() as db:
        with pytest.raises(Exception):
            app.state.alarm_manager.reload_saved_plugin(db)

    headers = _sign_in(client, caplog)
    public = client.get("/api/v1/setup/status").json()
    assert public == {"needs_admin": False, "has_alarm": True, "plugin_loaded": False}

    private = client.get("/api/v1/setup/status", headers=headers).json()
    assert "/dev/tty.nonexistent" in private["plugin_error"]


def test_reload_recovers_and_clears_the_error(client, app, session_factory, caplog):
    _save_alarm(session_factory, "plugins.Example.Simulated_Alarm", {})
    app.state.alarm_manager.last_load_error = "Plugin 'Saved' failed to load: device missing"
    headers = _sign_in(client, caplog)

    res = client.post("/api/v1/alarm/reload", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json() == {"status": "reloaded", "plugin": "Simulated Alarm"}

    status = client.get("/api/v1/setup/status", headers=headers).json()
    assert status["plugin_loaded"] is True and "plugin_error" not in status


def test_reload_without_saved_alarm_is_404(client, caplog):
    headers = _sign_in(client, caplog)
    assert client.post("/api/v1/alarm/reload", headers=headers).status_code == 404


def test_refresh_tokens_are_unique_within_the_same_second():
    assert security.create_refresh_token({"sub": "owner"}) != security.create_refresh_token({"sub": "owner"})
