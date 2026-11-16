from pathlib import Path

import pytest

from scguide.story import StoryError, bool_option, parse_story


def test_parse_story(tmp_path: Path):
    path = tmp_path / "story.md"
    path.write_text(
        """# Demo

@tool sketch.create
@click sketch=10,20
@type "20 mm" enter=false
@screenshot preview cursor=true
""",
        encoding="utf-8",
    )
    story = parse_story(path)
    assert [d.command for d in story.directives] == [
        "tool",
        "click",
        "type",
        "screenshot",
    ]
    assert story.directives[1].options == {"sketch": "10,20"}
    assert story.directives[2].positional == ("20 mm",)
    assert story.directives[2].options == {"enter": "false"}


def test_bool_option():
    assert bool_option("yes", name="x", line_number=1) is True
    assert bool_option("0", name="x", line_number=1) is False
    with pytest.raises(StoryError):
        bool_option("perhaps", name="x", line_number=1)
