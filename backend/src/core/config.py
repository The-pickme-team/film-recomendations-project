from pathlib import Path
from typing import Literal

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / 'config.yaml'


class ApiDatabaseSettings(BaseModel):
    """Database settings for the API section."""

    url: PostgresDsn
    pool_size: int = 50
    max_overflow: int = 100


class ApiSettings(BaseModel):
    """API settings loaded from YAML/ENV/secrets."""

    title: str = 'Backend API'
    version: str = '1.0.0'
    description: str = 'Backend API for film recommendations.'
    dev: bool = True
    database: ApiDatabaseSettings


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: Literal['debug', 'info', 'warning', 'error'] = 'info'


class AppSettings(BaseSettings):
    """Application settings loaded from YAML, env vars, and Docker secrets."""

    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        extra='ignore',
    )

    api: ApiSettings
    logging: LoggingSettings

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Priority: init > env > secrets > yaml > dotenv."""
        yaml_settings = YamlConfigSettingsSource(
            settings_cls,
            yaml_file=CONFIG_PATH,
            deep_merge=True,
        )
        return (
            init_settings,
            env_settings,
            file_secret_settings,
            yaml_settings,
            dotenv_settings,
        )


config = AppSettings()  # ty:ignore[missing-argument]
