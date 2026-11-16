# SolidCraft Guide experiment

Experimental tooling for writing a SolidCraft manual as ordinary Markdown while
driving the real SolidCraft UI to create reproducible screenshots.

The source document remains readable. Lines beginning with `@` are automation
directives and are removed from the generated manual.

```markdown
## Draw the base rectangle

Create a sketch on the XY plane.

@tool sketch.create
@click plane=XY

Choose Center Rectangle and place its centre at the origin.

@tool sketch.rectangle.center panel=family:Rectangle
@click sketch=0,0
@hover sketch=40,30
@assert tool=sketch.rectangle.center
@screenshot rectangle-preview

Click the second point to finish the rectangle.

@click sketch=40,30
@key Escape
@screenshot rectangle-finished
```

The important part of the preview screenshot is that the Rectangle tool is
still active: `@hover` moves the synthetic SolidCraft pointer without clicking,
and the screenshot is captured before the next action.

## Current MVP

Supported directives:

- `@tool COMMAND [panel=HANDLE]`
- `@click TARGET`
- `@hover TARGET`
- `@drag FROM TO [button=left|middle|right] [steps=N]`
- `@type "TEXT" [enter=true|false]`
- `@key KEY`
- `@view VIEW`
- `@wait SECONDS`
- `@assert tool=COMMAND`
- `@assert preview=true|false`
- `@assert dialog=TEXT`
- `@screenshot NAME [cursor=true|false] [mark=click|none]`

Targets are semantic where SolidCraft supports them:

```text
handle=toolbar:sketch.create
plane=XY
sketch=40,30
world=10,20,5
screen=900,500
```

`handle`, `plane`, `sketch`, and `world` are resolved through SolidCraft
`ui.at`. This is deliberately preferred over fixed screen coordinates.

## Run

Start SolidCraft with its control channel enabled:

```text
solidcraft --control 7878
```

Install the experiment:

```text
python -m pip install -e .
```

Then run a story. On Windows, set the capture rectangle to the SolidCraft
window or to the monitor region containing it:

```text
scguide examples/basic-box.guide.md --out build/basic-box --port 7878 \
  --region 0,0,1920,1080
```

The result is:

```text
build/basic-box/
  guide.md
  images/
    01-sketch-open.png
    02-rectangle-preview.png
    ...
  run.jsonl
```

The generated `guide.md` contains the prose from the story and image links in
place of each `@screenshot` directive.

## Cursor coordinates

SolidCraft UI coordinates are normally window-local. Capture coordinates are
screen coordinates. If the SolidCraft client area starts at screen position
`(x, y)`, pass:

```text
--ui-origin x,y
```

The screenshot overlay then maps the synthetic cursor into the captured image.
For a maximized app beginning at the capture region's top-left, the default
`0,0` is sufficient when `--region` also begins there.

Automatic window discovery is intentionally postponed until the first working
manual proves which Windows capture path is most reliable.

## Why a separate experiment?

This repository intentionally mixes the guide language, UI automation, capture
code and sample manuals. Once the useful boundary is clear it can be split into
a reusable tool repository and one or more manual/content repositories.

## SolidCraft reference

The approach is based on SolidCraft's own demo strategy: its Raspberry Pi demo
drives the real UI over the control channel and records pointer/caption events.
This experiment does not copy that demo wholesale; it uses the same public
control concepts (`ui.at`, `ui.move`, `ui.click`, `ui.drag`, `ui.inspect`,
`ui.handles`) to produce static documentation screenshots instead of a video.
