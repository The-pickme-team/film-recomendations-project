from pathlib import Path

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource


class OpenAPIConfig(BaseModel):
    title: str
    version: str
    description: str


class CorsConfig(BaseModel):
    allowed_origins: list[str]
    allowed_methods: list[str]
    allowed_headers: list[str]


class AppConfig(BaseModel):
    openapi: OpenAPIConfig
    cors: CorsConfig


class DatabaseUrlConfig(BaseModel):
    driver: str
    username: str
    password: SecretStr
    host: str
    port: int
    database: str

    def composite(self) -> str:
        return f"{self.driver}://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.database}"


class DatabaseConfig(BaseModel):
    url: DatabaseUrlConfig
    pool_size: int = 20
    max_overflow: int = 30


class LoggingConfig(BaseModel):
    level: str = "INFO"


class Settings(BaseSettings):
    app: AppConfig
    database: DatabaseConfig
    logging: LoggingConfig

    model_config = SettingsConfigDict(
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
        env_nested_delimiter="__",
        # secrets_dir="/run/secrets",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        Переопределяем порядок источников:
        1. Явная передача в конструктор (init_settings)
        2. Переменные окружения (env_settings)
        3. Docker-секреты из файлов (file_secret_settings)
        4. YAML-файл (YamlConfigSettingsSource)
        """
        return (
            init_settings,
            env_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )


config = Settings()  # ty:ignore[missing-argument]
