from __future__ import annotations

from pathlib import Path

from .story import Story


def render_markdown(story: Story, screenshots: dict[int, tuple[str, str]]) -> str:
    """Remove action directives and replace screenshot directives with images.

    screenshots maps source line number -> (name, relative path).
    """
    output: list[str] = []
    for line_number, line in enumerate(story.lines, 1):
        stripped = line.lstrip()
        if not stripped.startswith("@"):
            output.append(line)
            continue
        if line_number in screenshots:
            name, relative = screenshots[line_number]
            output.append(f"![{name}]({relative})")
    return "\n".join(output).rstrip() + "\n"


def write_markdown(
    story: Story,
    screenshots: dict[int, tuple[str, str]],
    destination: str | Path,
) -> None:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_markdown(story, screenshots),
        encoding="utf-8",
    )
