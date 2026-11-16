from __future__ import annotations

import argparse
from pathlib import Path

from .capture import Region
from .control import ControlClient
from .driver import SolidCraftDriver
from .runner import GuideRunner
from .story import parse_story


def _pair(raw: str) -> tuple[int, int]:
    try:
        values = tuple(int(x.strip()) for x in raw.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected x,y") from exc
    if len(values) != 2:
        raise argparse.ArgumentTypeError("expected x,y")
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Drive SolidCraft from a Markdown story and generate screenshots."
    )
    parser.add_argument("story", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--port", type=int, default=7878)
    parser.add_argument(
        "--region",
        type=Region.parse,
        help="screen capture rectangle: left,top,width,height",
    )
    parser.add_argument(
        "--ui-origin",
        type=_pair,
        default=(0, 0),
        help="SolidCraft client-area origin in screen coordinates: x,y",
    )
    args = parser.parse_args(argv)

    story = parse_story(args.story)
    driver = SolidCraftDriver(ControlClient(port=args.port))
    destination = GuideRunner(
        driver,
        output=args.out,
        region=args.region,
        ui_origin=args.ui_origin,
    ).run(story)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
