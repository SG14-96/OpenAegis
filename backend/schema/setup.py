from pydantic import BaseModel, Field, field_validator


class SetupStatus(BaseModel):
    """
    GET /api/v1/setup/status — which first-run state the app is in. Public,
    so the frontend can route before anyone has signed in.
    """
    # No users exist; the setup wizard must create the first admin.
    needs_admin: bool
    # An alarm configuration has been saved.
    has_alarm: bool
    # The saved alarm's plugin is loaded and running right now.
    plugin_loaded: bool
    # Why the plugin isn't running (e.g. serial port missing at boot). Only
    # included for signed-in users — it can contain device paths.
    plugin_error: str | None = None


class FirstAdminCreate(BaseModel):
    """POST /api/v1/setup/admin body."""
    setup_code: str
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    email: str | None = None
    full_name: str | None = None

    @field_validator("username")
    @classmethod
    def _strip_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be blank.")
        return v
