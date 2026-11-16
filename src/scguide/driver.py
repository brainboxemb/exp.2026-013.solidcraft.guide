from __future__ import annotations

import json
import math
import time

from .control import ControlClient
from .story import Directive, StoryError, bool_option


def _numbers(value: str, count: int, *, line_number: int) -> list[float]:
    try:
        values = [float(x.strip()) for x in value.split(",")]
    except ValueError as exc:
        raise StoryError(
            f"line {line_number}: expected comma-separated numbers, got {value!r}"
        ) from exc
    if len(values) != count or not all(math.isfinite(x) for x in values):
        raise StoryError(
            f"line {line_number}: expected {count} finite values, got {value!r}"
        )
    return values


class SolidCraftDriver:
    def __init__(self, client: ControlClient):
        self.client = client
        self.position: tuple[float, float] | None = None

    def ui(self, method: str, params: dict | None = None):
        return self.client.call(method, params)

    def inspect(self) -> dict:
        return self.ui("ui.inspect") or {}

    def settle(self, timeout: float = 15.0) -> None:
        deadline = time.monotonic() + timeout
        last = None
        stable = 0
        while time.monotonic() < deadline:
            state = self.inspect()
            snapshot = json.dumps(
                [
                    state.get("camera"),
                    state.get("tool"),
                    state.get("dialog"),
                    self.ui("ui.handles"),
                ],
                sort_keys=True,
            )
            busy = bool((state.get("preview") or {}).get("busy", False))
            stable = stable + 1 if snapshot == last and not busy else 0
            last = snapshot
            if stable >= 2:
                return
            time.sleep(0.1)
        raise RuntimeError("SolidCraft UI did not settle")

    def locate(self, directive: Directive, token: str | None = None) -> tuple[float, float]:
        options = directive.options
        if token is not None:
            if ":" not in token:
                raise StoryError(
                    f"line {directive.line_number}: target must be kind:value"
                )
            kind, value = token.split(":", 1)
            options = {kind: value}

        locators = [k for k in ("handle", "plane", "sketch", "world", "screen") if k in options]
        if len(locators) != 1:
            raise StoryError(
                f"line {directive.line_number}: expected exactly one target "
                f"(handle, plane, sketch, world or screen)"
            )

        kind = locators[0]
        value = options[kind]
        if kind == "screen":
            x, y = _numbers(value, 2, line_number=directive.line_number)
            return x, y
        if kind == "sketch":
            payload = {"sketch": _numbers(value, 2, line_number=directive.line_number)}
        elif kind == "world":
            payload = {"world": _numbers(value, 3, line_number=directive.line_number)}
        else:
            payload = {kind: value}
        point = self.ui("ui.at", payload)
        if not isinstance(point, list) or len(point) < 2:
            raise RuntimeError(f"ui.at {payload} returned invalid point {point!r}")
        return float(point[0]), float(point[1])

    def move(self, to: tuple[float, float], duration: float = 0.25) -> None:
        start = self.position or to
        steps = max(2, int(duration * 40))
        for index in range(1, steps + 1):
            t = index / steps
            eased = t * t * (3 - 2 * t)
            x = start[0] + (to[0] - start[0]) * eased
            y = start[1] + (to[1] - start[1]) * eased
            self.ui("ui.move", {"x": x, "y": y})
            time.sleep(duration / steps)
        self.position = to

    def click(self, to: tuple[float, float]) -> None:
        self.move(to)
        self.ui("ui.click", {"x": to[0], "y": to[1]})
        self.position = to
        self.settle()

    def hover(self, to: tuple[float, float]) -> None:
        self.move(to)
        self.settle()

    def drag(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        button: str = "left",
        steps: int = 30,
    ) -> None:
        self.move(start)
        self.ui(
            "ui.drag",
            {
                "x0": start[0],
                "y0": start[1],
                "x1": end[0],
                "y1": end[1],
                "button": button,
                "steps": steps,
            },
        )
        self.position = end
        self.settle()

    def tool(self, command: str, panel: str | None = None) -> None:
        self.settle()
        handles = self.ui("ui.handles") or []
        names = {h.get("name") for h in handles if isinstance(h, dict)}
        target = f"toolbar:{command}"
        if panel and target not in names:
            self.click(self._at_handle(panel))
        self.click(self._at_handle(target))

    def _at_handle(self, handle: str) -> tuple[float, float]:
        point = self.ui("ui.at", {"handle": handle})
        if not isinstance(point, list) or len(point) < 2:
            raise RuntimeError(f"handle {handle!r} is not available")
        return float(point[0]), float(point[1])

    def type_text(self, text: str, *, enter: bool = True) -> None:
        self.ui("ui.text", {"text": text})
        if enter:
            self.ui("ui.key", {"key": "Enter"})
            self.settle()

    def key(self, key: str) -> None:
        self.ui("ui.key", {"key": key})
        self.settle()

    def view(self, view: str) -> None:
        self.ui("ui.view", {"view": view, "animate": True})
        self.settle()

    def assert_state(self, directive: Directive) -> None:
        state = self.inspect()
        for key, expected in directive.options.items():
            if key == "tool":
                actual = state.get("tool")
                if actual != expected:
                    raise AssertionError(
                        f"line {directive.line_number}: tool is {actual!r}, "
                        f"expected {expected!r}"
                    )
            elif key == "preview":
                actual = bool((state.get("preview") or {}).get("busy", False))
                wanted = bool_option(expected, name="preview", line_number=directive.line_number)
                if actual != wanted:
                    raise AssertionError(
                        f"line {directive.line_number}: preview busy={actual}, "
                        f"expected {wanted}"
                    )
            elif key == "dialog":
                actual = str(state.get("dialog") or "")
                if expected not in actual:
                    raise AssertionError(
                        f"line {directive.line_number}: dialog {actual!r} "
                        f"does not contain {expected!r}"
                    )
            else:
                raise StoryError(
                    f"line {directive.line_number}: unsupported @assert key {key!r}"
                )
