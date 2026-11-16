from pathlib import Path

from scguide.render import render_markdown
from scguide.story import parse_story


def test_render_removes_actions_and_inserts_images(tmp_path: Path):
    path = tmp_path / "story.md"
    path.write_text(
        """# Demo

Do this.

@click plane=XY
@screenshot active-tool

Then continue.
""",
        encoding="utf-8",
    )
    story = parse_story(path)
    screenshot_line = next(
        d.line_number for d in story.directives if d.command == "screenshot"
    )
    rendered = render_markdown(
        story,
        {screenshot_line: ("active-tool", "images/01-active-tool.png")},
    )
    assert "@click" not in rendered
    assert "@screenshot" not in rendered
    assert "![active-tool](images/01-active-tool.png)" in rendered
    assert "Then continue." in rendered
