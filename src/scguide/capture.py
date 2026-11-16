from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math


@dataclass(frozen=True)
class Region:
    left: int
    top: int
    width: int
    height: int

    @classmethod
    def parse(cls, raw: str) -> "Region":
        try:
            values = [int(x.strip()) for x in raw.split(",")]
        except ValueError as exc:
            raise ValueError("--region must be left,top,width,height") from exc
        if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
            raise ValueError("--region must be left,top,width,height with positive size")
        return cls(*values)


def capture_screen(region: Region | None):
    import mss
    from PIL import Image

    with mss.mss() as screen:
        monitor = (
            {
                "left": region.left,
                "top": region.top,
                "width": region.width,
                "height": region.height,
            }
            if region
            else screen.monitors[1]
        )
        shot = screen.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.rgb), Region(
            monitor["left"], monitor["top"], monitor["width"], monitor["height"]
        )


def _cursor_polygon(x: float, y: float) -> list[tuple[float, float]]:
    return [
        (x, y),
        (x, y + 24),
        (x + 6, y + 18),
        (x + 11, y + 28),
        (x + 15, y + 26),
        (x + 10, y + 17),
        (x + 19, y + 17),
    ]


def overlay_pointer(
    image,
    *,
    ui_position: tuple[float, float] | None,
    capture_region: Region,
    ui_origin: tuple[int, int] = (0, 0),
    mark_click: bool = False,
):
    from PIL import ImageDraw

    if ui_position is None:
        return image
    x = ui_origin[0] + ui_position[0] - capture_region.left
    y = ui_origin[1] + ui_position[1] - capture_region.top

    draw = ImageDraw.Draw(image, "RGBA")
    polygon = _cursor_polygon(x, y)
    draw.line(polygon + [polygon[0]], fill=(0, 0, 0, 255), width=4, joint="curve")
    draw.polygon(polygon, fill=(255, 255, 255, 245))
    draw.line(polygon + [polygon[0]], fill=(20, 20, 20, 255), width=2, joint="curve")

    if mark_click:
        radius = 22
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            outline=(70, 150, 255, 230),
            width=4,
        )
    return image


def save_png(image, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")
