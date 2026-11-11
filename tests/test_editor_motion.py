"""Motion: entrance/exit presets and keyframes on a clip, plus the named Effect set.

Emitted only when set, like ``filter`` and ``lut``, so existing timelines serialize
exactly as before.
"""

import pytest

from videodb.editor import (
    Clip, Easing, Effect, Keyframe, KeyframeProperty, Motion, MotionPreset, VideoAsset,
)


def test_preset_defaults_and_json():
    assert MotionPreset("slide_up").to_json() == {
        "preset": "slide_up", "duration": 0.4, "amount": 0.08, "easing": "ease_out",
    }
    custom = MotionPreset(preset="pop", duration=1, amount=0.2, easing="back_out")
    assert custom.to_json()["preset"] == "pop" and custom.easing is Easing.back_out


@pytest.mark.parametrize("kwargs", [dict(duration=0), dict(duration=11), dict(amount=1.5), dict(preset="bounce")])
def test_preset_validation(kwargs):
    with pytest.raises(ValueError):
        MotionPreset(**{"preset": "fade", **kwargs})


def test_keyframe_json_and_validation():
    assert Keyframe(0.5, 1, Easing.ease_in).to_json() == {"time": 0.5, "value": 1, "easing": "ease_in"}
    assert Keyframe(0, 0).to_json()["easing"] == "linear"
    with pytest.raises(ValueError):
        Keyframe(-1, 0)


def test_motion_json_emits_only_set_parts():
    assert Motion().to_json() == {}
    motion = Motion(
        enter=MotionPreset("fade"),
        keyframes={"scale": [Keyframe(0, 0.8), Keyframe(0.5, 1, "back_out")], KeyframeProperty.rotation: [Keyframe(0, 0)]},
    )
    assert motion.to_json() == {
        "enter": {"preset": "fade", "duration": 0.4, "amount": 0.08, "easing": "ease_out"},
        "keyframes": {
            "scale": [{"time": 0, "value": 0.8, "easing": "linear"}, {"time": 0.5, "value": 1, "easing": "back_out"}],
            "rotation": [{"time": 0, "value": 0, "easing": "linear"}],
        },
    }


@pytest.mark.parametrize("keyframes", [
    {"colour": [Keyframe(0, 1)]},
    {"scale": []},
    {"scale": [Keyframe(1, 1), Keyframe(1, 2)]},
])
def test_motion_keyframe_validation(keyframes):
    with pytest.raises(ValueError):
        Motion(keyframes=keyframes)


def test_clip_emits_motion_and_effect_only_when_set():
    asset = VideoAsset(id="m-1")
    plain = Clip(asset=asset, duration=5).to_json()
    assert "motion" not in plain and plain["effect"] is None
    animated = Clip(asset=asset, duration=5, motion=Motion(exit=MotionPreset("wipe_left"))).to_json()
    assert animated["motion"] == {"exit": {"preset": "wipe_left", "duration": 0.4, "amount": 0.08, "easing": "ease_out"}}
    assert Clip(asset=asset, duration=5, effect=Effect.ken_burns).to_json()["effect"] == "ken_burns"
    assert Clip(asset=asset, duration=5, effect="zoom_in").to_json()["effect"] == "zoom_in"
