from scguide.driver import SolidCraftDriver
from scguide.story import Directive


class FakeClient:
    def call(self, method, params=None):
        if method == "ui.at":
            if "sketch" in params:
                return [400, 300]
            if "world" in params:
                return [800, 600]
            return [100, 50]
        if method == "ui.inspect":
            return {
                "tool": "sketch.rectangle.center",
                "dialog": "",
                "preview": {"busy": False},
                "camera": {"yaw": 0},
            }
        if method == "ui.handles":
            return []
        return {}


def directive(raw, **options):
    return Directive("click", (), options, 1, raw)


def test_semantic_locator():
    driver = SolidCraftDriver(FakeClient())
    assert driver.locate(directive("@click sketch=1,2", sketch="1,2")) == (400, 300)
    assert driver.locate(directive("@click world=1,2,3", world="1,2,3")) == (800, 600)
    assert driver.locate(directive("@click handle=x", handle="x")) == (100, 50)


def test_state_assertion():
    driver = SolidCraftDriver(FakeClient())
    driver.assert_state(
        Directive(
            "assert",
            (),
            {"tool": "sketch.rectangle.center", "preview": "false"},
            1,
            "@assert tool=sketch.rectangle.center preview=false",
        )
    )
