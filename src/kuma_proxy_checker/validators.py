from pathlib import Path
from typing import Any

from pydantic_core import PydanticCustomError

from .templates import ALLOWED_VAR_NAMES, TEMPLATE_PATTERN


def validate_template_vars(obj: Any, path: str = "$") -> None:
    if isinstance(obj, str):
        used = {m.group(1) for m in TEMPLATE_PATTERN.finditer(obj)}
        invalid = used - ALLOWED_VAR_NAMES
        if invalid:
            raise ValueError(
                f"{path}: disallowed template variables: {invalid}. Allowed: {sorted(ALLOWED_VAR_NAMES)}"
            )
    elif isinstance(obj, dict):
        for k, v in obj.items():
            validate_template_vars(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            validate_template_vars(v, f"{path}[{i}]")


def validate_ssl_files(v: str | None, ssl_enabled: bool) -> str | None:
    if v and ssl_enabled:
        if not Path(v).is_file():
            raise PydanticCustomError(
                "ssl_file_not_found",
                "SSL file not found: {path}",
                {"path": v},
            )
    return v
