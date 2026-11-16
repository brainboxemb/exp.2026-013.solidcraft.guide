from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex


class StoryError(ValueError):
    pass


@dataclass(frozen=True)
class Directive:
    command: str
    positional: tuple[str, ...]
    options: dict[str, str]
    line_number: int
    raw: str


@dataclass(frozen=True)
class Story:
    path: Path
    lines: tuple[str, ...]
    directives: tuple[Directive, ...]


def _parse_tokens(raw: str, line_number: int) -> Directive:
    try:
        tokens = shlex.split(raw, posix=True)
    except ValueError as exc:
        raise StoryError(f"line {line_number}: {exc}") from exc
    if not tokens or not tokens[0].startswith("@"):
        raise StoryError(f"line {line_number}: not a directive")
    command = tokens[0][1:].strip()
    if not command:
        raise StoryError(f"line {line_number}: empty directive")

    positional: list[str] = []
    options: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            if not key:
                raise StoryError(f"line {line_number}: empty option name")
            options[key] = value
        else:
            positional.append(token)
    return Directive(command, tuple(positional), options, line_number, raw)


def parse_story(path: str | Path) -> Story:
    path = Path(path)
    lines = tuple(path.read_text(encoding="utf-8").splitlines())
    directives = tuple(
        _parse_tokens(line.strip(), i)
        for i, line in enumerate(lines, 1)
        if line.lstrip().startswith("@")
    )
    return Story(path, lines, directives)


def bool_option(value: str, *, name: str, line_number: int) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise StoryError(
        f"line {line_number}: {name} must be true or false, got {value!r}"
    )
