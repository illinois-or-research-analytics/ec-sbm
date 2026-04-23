"""Per-stage params.txt helpers.

Format: one `key=value` per line, sorted keys, bools as `true`/`false`.
Values are stringified on write; the reader returns `dict[str, str]` and
callers coerce types.
"""
from __future__ import annotations

from pathlib import Path


def _render(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_params(out_dir, **kwargs) -> None:
    """Write params.txt to out_dir. At least one kwarg required."""
    if not kwargs:
        raise ValueError("write_params: at least one key=value required")
    out_path = Path(out_dir) / "params.txt"
    lines = [f"{k}={_render(kwargs[k])}" for k in sorted(kwargs)]
    out_path.write_text("\n".join(lines) + "\n")


def resolve_param(cli_value, file_params: dict[str, str] | None, key: str,
                  default=None, parser=None):
    """CLI > file > default. `parser` coerces file values (CLI values pass through)."""
    if cli_value is not None:
        return cli_value
    if file_params is not None and key in file_params:
        raw = file_params[key]
        return parser(raw) if parser else raw
    return default


def _parse_bool(text: str) -> bool:
    if text == "true":
        return True
    if text == "false":
        return False
    raise ValueError(f"expected 'true' or 'false', got {text!r}")


def read_params(path) -> dict[str, str]:
    """Read params.txt → dict. Raises on malformed lines or duplicate keys."""
    text = Path(path).read_text()
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"{path}: expected key=value, got {raw!r}")
        key, value = line.split("=", 1)
        if key in out:
            raise ValueError(f"{path}: duplicate key {key!r}")
        out[key] = value
    return out
