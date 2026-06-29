from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    scope = Column(String, unique=True, nullable=False)
    data = Column(JSONB, nullable=False, default=dict)


class AlarmSettings(Base):
    __tablename__ = "alarm_settings"

    id = Column(Integer, primary_key=True)
    alarm_name = Column(String, unique=True, nullable=False)
    data = Column(JSONB, nullable=False, default=dict)

    plugin_settings = relationship(
        "PluginSettings",
        back_populates="alarm",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PluginSettings(Base):
    __tablename__ = "plugin_settings"

    id = Column(Integer, primary_key=True)
    plugin_name = Column(String, unique=True, nullable=False)
    is_currently_used = Column(Boolean, default=False)
    data = Column(JSONB, nullable=False, default=dict)
    alarm_settings_id = Column(
        Integer, ForeignKey("alarm_settings.id", ondelete="CASCADE"), nullable=True
    )

    alarm = relationship("AlarmSettings", back_populates="plugin_settings")
