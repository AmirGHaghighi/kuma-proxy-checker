from pydantic import AnyUrl, BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from .models import ProxyScheme


class ProxyTarget(BaseModel):
    proxy: AnyUrl
    push_url: AnyUrl
    remark: str | None = None

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


class AppConfig(BaseModel):
    test_url: AnyUrl
    expected_status: int = Field(ge=100, le=599)
    retries: int = Field(ge=1, default=3)
    timeout_seconds: float = Field(gt=0, default=10.0)
    retry_delay_seconds: float = Field(ge=0, default=1.0)
    interval_minutes: int = Field(ge=0, default=5)
    targets: list[ProxyTarget] = Field(min_length=1)

    @classmethod
    def from_file(cls, path: str) -> "AppConfig":
        with open(path) as f:
            return cls.model_validate_json(f.read())
