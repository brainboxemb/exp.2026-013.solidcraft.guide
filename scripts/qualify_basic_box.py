from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

from PIL import Image

import scguide.runner as runner_module
from scguide.capture import Region
from scguide.runner import GuideRunner
from scguide.story import Directive, parse_story


ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / "examples" / "basic-box.guide.md"
OUTPUT = ROOT / "build" / "qualification" / "basic-box"


class OfflineSolidCraftDriver:
    """Small deterministic stand-in for the SolidCraft UI.

    This qualification intentionally exercises the real story parser, GuideRunner,
    screenshot naming/overlay path, run log, and Markdown renderer on GitHub.
    It does not claim to validate SolidCraft's real control channel or window.
    """

    def __init__(self) -> None:
        self.position: tuple[float, float] | None = None
        self.tool_name: str | None = None

    def settle(self) -> None:
        pass

    def locate(
        self, directive: Directive, token: str | None = None
    ) -> tuple[float, float]:
        if token:
            kind, value = token.split(":", 1)
        else:
            found = [
                (key, directive.options[key])
                for key in ("handle", "plane", "sketch", "world", "screen")
                if key in directive.options
            ]
            if len(found) != 1:
                raise AssertionError(
                    f"line {directive.line_number}: expected one target, got {found!r}"
                )
            kind, value = found[0]

        if kind == "plane":
            return (320.0, 240.0)
        if kind == "sketch":
            x, y = (float(part) for part in value.split(","))
            return (320.0 + x * 3.0, 240.0 - y * 3.0)
        if kind == "screen":
            x, y = (float(part) for part in value.split(","))
            return (x, y)
        if kind in {"handle", "world"}:
            return (360.0, 260.0)
        raise AssertionError(f"unsupported offline target {kind!r}")

    def tool(self, command: str, panel: str | None = None) -> None:
        self.tool_name = command
        self.position = (120.0, 80.0)

    def click(self, to: tuple[float, float]) -> None:
        self.position = to

    def hover(self, to: tuple[float, float]) -> None:
        self.position = to

    def drag(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        button: str = "left",
        steps: int = 30,
    ) -> None:
        self.position = end

    def type_text(self, text: str, *, enter: bool = True) -> None:
        pass

    def key(self, key: str) -> None:
        if key.lower() == "escape":
            self.tool_name = None

    def view(self, view: str) -> None:
        pass

    def assert_state(self, directive: Directive) -> None:
        expected = directive.options.get("tool")
        if expected is not None and self.tool_name != expected:
            raise AssertionError(
                f"line {directive.line_number}: tool is {self.tool_name!r}, "
                f"expected {expected!r}"
            )


def fake_capture(region: Region | None):
    actual = region or Region(0, 0, 640, 480)
    image = Image.new("RGB", (actual.width, actual.height), (245, 245, 245))
    return image, actual


def main() -> int:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    story = parse_story(STORY)
    runner_module.capture_screen = fake_capture

    destination = GuideRunner(
        OfflineSolidCraftDriver(),
        output=OUTPUT,
        region=Region(0, 0, 640, 480),
    ).run(story)

    images = sorted((OUTPUT / "images").glob("*.png"))
    if len(images) != 4:
        raise AssertionError(f"expected 4 screenshots, found {len(images)}")

    markdown = destination.read_text(encoding="utf-8")
    if any(line.lstrip().startswith("@") for line in markdown.splitlines()):
        raise AssertionError("generated guide still contains automation directives")
    if markdown.count("images/") != 4:
        raise AssertionError("generated guide does not reference all screenshots")

    log_events = [
        json.loads(line)
        for line in (OUTPUT / "run.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(log_events) != len(story.directives):
        raise AssertionError(
            f"run log has {len(log_events)} events for "
            f"{len(story.directives)} directives"
        )

    print(f"qualified: {STORY.relative_to(ROOT)}")
    print(f"directives: {len(story.directives)}")
    print(f"screenshots: {len(images)}")
    print(f"guide: {destination.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
