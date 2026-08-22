
from pydantic import AnyUrl, BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from .models import ProxyScheme
from .validators import validate_ssl_files, validate_template_vars


class ProxyTarget(BaseModel):
    proxy: AnyUrl
    push_url: AnyUrl
    remark: str | None = None
    test_url: AnyUrl | None = None

    @field_validator("proxy")
    @classmethod
    def validate_proxy_scheme(cls, v: AnyUrl) -> AnyUrl:
        allowed = {s.value for s in ProxyScheme}
        if v.scheme not in allowed:
            raise PydanticCustomError(
                "invalid_proxy_scheme",
                "Unsupported proxy scheme: {scheme}. Allowed: {allowed}",
                {"scheme": v.scheme, "allowed": allowed},
            )
        return v


class HealthCheckConfig(BaseModel):
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = Field(ge=0, le=65535, default=8080)
    path: str = "/health"
    response_code: int = Field(ge=100, le=599, default=200)
    response_json: dict = Field(default_factory=lambda: {"status": "ok"})
    ssl_enabled: bool = False
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None

    @field_validator("response_json")
    @classmethod
    def validate_response_json_template(cls, v: dict) -> dict:
        validate_template_vars(v)
        return v

    @field_validator("ssl_certfile", "ssl_keyfile")
    @classmethod
    def validate_ssl_files(cls, v: str | None, info) -> str | None:
        return validate_ssl_files(v, info.data.get("ssl_enabled", False))


class AppConfig(BaseModel):
    default_test_url: AnyUrl
    expected_status: int = Field(ge=100, le=599)
    retries: int = Field(ge=1, default=3)
    timeout_seconds: float = Field(gt=0, default=10.0)
    retry_delay_seconds: float = Field(ge=0, default=1.0)
    interval_minutes: int = Field(ge=0, default=5)
    notifier_timeout_seconds: float = Field(gt=0, default=10.0)
    targets: list[ProxyTarget] = Field(min_length=1)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        with open(path) as f:
            return cls.model_validate_json(f.read())
