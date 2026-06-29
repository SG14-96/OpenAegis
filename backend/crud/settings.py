from sqlalchemy.orm import Session

from models.settings import Settings, AlarmSettings, PluginSettings


def get_active_plugin_settings(db: Session) -> PluginSettings | None:
    return (
        db.query(PluginSettings)
        .filter(PluginSettings.is_currently_used == True)  # noqa: E712
        .first()
    )


def persist_plugin_config(
    db: Session,
    plugin_name: str,
    module_path: str,
    setup_values: dict | None,
) -> PluginSettings:
    """Mark all plugin rows inactive, then upsert the given plugin as active."""
    db.query(PluginSettings).update({"is_currently_used": False})

    record = (
        db.query(PluginSettings)
        .filter(PluginSettings.plugin_name == plugin_name)
        .first()
    )
    if record is None:
        record = PluginSettings(plugin_name=plugin_name)
        db.add(record)

    record.is_currently_used = True
    record.data = {"module_path": module_path, "setup_values": setup_values or {}}
    db.commit()
    db.refresh(record)
    return record


def get_alarm_settings(db: Session) -> AlarmSettings | None:
    return db.query(AlarmSettings).first()


def create_alarm_settings(db: Session, alarm_name: str, plugin_settings: PluginSettings) -> AlarmSettings:
    record = AlarmSettings(alarm_name=alarm_name, data={}, plugin_settings=plugin_settings)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_alarm_settings(db: Session, alarm_name: str | None) -> AlarmSettings:
    record = db.query(AlarmSettings).first()
    if record is None:
        raise ValueError("No alarm settings record found.")
    if alarm_name is not None:
        record.alarm_name = alarm_name
    db.commit()
    db.refresh(record)
    return record


def delete_alarm_settings(db: Session) -> None:
    record = db.query(AlarmSettings).first()
    if record is not None:
        db.delete(record)
        db.commit()


def save_alarm_settings(db: Session, data: dict) -> None:
    record = db.query(AlarmSettings).first()
    if record is None:
        record = AlarmSettings(data=data)
        db.add(record)
    else:
        record.data = data
    db.commit()


def get_settings(db: Session) -> Settings | None:
    return db.query(Settings).first()


def upsert_settings(db: Session, scope: str, data: dict) -> Settings:
    record = db.query(Settings).filter(Settings.scope == scope).first()
    if record is None:
        record = Settings(scope=scope, data=data)
        db.add(record)
    else:
        record.data = data
    db.commit()
    db.refresh(record)
    return record
