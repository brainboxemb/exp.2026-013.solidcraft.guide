from __future__ import annotations

import json
from pathlib import Path
import time

from .capture import Region, capture_screen, overlay_pointer, save_png
from .driver import SolidCraftDriver
from .render import write_markdown
from .story import Directive, Story, StoryError, bool_option


class GuideRunner:
    def __init__(
        self,
        driver: SolidCraftDriver,
        *,
        output: str | Path,
        region: Region | None,
        ui_origin: tuple[int, int] = (0, 0),
    ):
        self.driver = driver
        self.output = Path(output)
        self.region = region
        self.ui_origin = ui_origin
        self.images = self.output / "images"
        self.log_path = self.output / "run.jsonl"
        self._screenshots: dict[int, tuple[str, str]] = {}
        self._shot_index = 0

    def _log(self, directive: Directive, **extra) -> None:
        self.output.mkdir(parents=True, exist_ok=True)
        event = {
            "time": time.time(),
            "line": directive.line_number,
            "command": directive.command,
            "raw": directive.raw,
            **extra,
        }
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    def run(self, story: Story) -> Path:
        self.output.mkdir(parents=True, exist_ok=True)
        if self.log_path.exists():
            self.log_path.unlink()

        for directive in story.directives:
            self._execute(directive)

        destination = self.output / "guide.md"
        write_markdown(story, self._screenshots, destination)
        return destination

    def _execute(self, d: Directive) -> None:
        cmd = d.command
        if cmd == "tool":
            if len(d.positional) != 1:
                raise StoryError(f"line {d.line_number}: @tool requires one command")
            self.driver.tool(d.positional[0], d.options.get("panel"))
        elif cmd in {"click", "hover"}:
            target = d.positional[0] if d.positional else None
            point = self.driver.locate(d, target)
            getattr(self.driver, cmd)(point)
        elif cmd == "drag":
            if len(d.positional) != 2:
                raise StoryError(
                    f"line {d.line_number}: @drag requires FROM and TO targets"
                )
            start = self.driver.locate(d, d.positional[0])
            end = self.driver.locate(d, d.positional[1])
            button = d.options.get("button", "left")
            steps = int(d.options.get("steps", "30"))
            self.driver.drag(start, end, button=button, steps=steps)
        elif cmd == "type":
            if len(d.positional) != 1:
                raise StoryError(f"line {d.line_number}: @type requires quoted text")
            enter = bool_option(
                d.options.get("enter", "true"),
                name="enter",
                line_number=d.line_number,
            )
            self.driver.type_text(d.positional[0], enter=enter)
        elif cmd == "key":
            if len(d.positional) != 1:
                raise StoryError(f"line {d.line_number}: @key requires one key")
            self.driver.key(d.positional[0])
        elif cmd == "view":
            if len(d.positional) != 1:
                raise StoryError(f"line {d.line_number}: @view requires one view")
            self.driver.view(d.positional[0])
        elif cmd == "wait":
            if len(d.positional) != 1:
                raise StoryError(f"line {d.line_number}: @wait requires seconds")
            time.sleep(float(d.positional[0]))
        elif cmd == "assert":
            self.driver.assert_state(d)
        elif cmd == "screenshot":
            self._screenshot(d)
        else:
            raise StoryError(f"line {d.line_number}: unknown directive @{cmd}")
        self._log(d, cursor=self.driver.position)

    def _screenshot(self, d: Directive) -> None:
        if len(d.positional) != 1:
            raise StoryError(f"line {d.line_number}: @screenshot requires one name")
        self.driver.settle()
        name = d.positional[0]
        show_cursor = bool_option(
            d.options.get("cursor", "true"),
            name="cursor",
            line_number=d.line_number,
        )
        mark = d.options.get("mark", "none")
        if mark not in {"none", "click"}:
            raise StoryError(
                f"line {d.line_number}: screenshot mark must be none or click"
            )

        image, actual_region = capture_screen(self.region)
        if show_cursor:
            overlay_pointer(
                image,
                ui_position=self.driver.position,
                capture_region=actual_region,
                ui_origin=self.ui_origin,
                mark_click=mark == "click",
            )

        self._shot_index += 1
        filename = f"{self._shot_index:02d}-{name}.png"
        save_png(image, self.images / filename)
        self._screenshots[d.line_number] = (name, f"images/{filename}")
