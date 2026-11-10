"""Lut: 3D .cube colour grades on a clip or the whole timeline.

The field is emitted only when set, like ``filter``, so timelines without a LUT
serialize exactly as before.
"""

from unittest import mock

import pytest

from videodb.editor import Clip, Lut, Timeline, Track, VideoAsset
from videodb.exceptions import InvalidRequestError

CUBE_URL = "https://storage.example/grade.cube"


def test_lut_to_json_and_defaults():
    assert Lut(CUBE_URL).to_json() == {"src": CUBE_URL, "intensity": 1.0}
    assert Lut(CUBE_URL, intensity=0.4).to_json() == {"src": CUBE_URL, "intensity": 0.4}


@pytest.mark.parametrize("bad", [-0.1, 1.5])
def test_lut_intensity_bounds(bad):
    with pytest.raises(ValueError, match="intensity"):
        Lut(CUBE_URL, intensity=bad)


def test_clip_emits_lut_only_when_set():
    asset = VideoAsset(id="m-1")
    assert "lut" not in Clip(asset=asset, duration=5).to_json()
    graded = Clip(asset=asset, duration=5, lut=Lut(CUBE_URL, intensity=0.5)).to_json()
    assert graded["lut"] == {"src": CUBE_URL, "intensity": 0.5}


def test_timeline_emits_lut_only_when_set():
    timeline = Timeline(connection=None)
    track = Track()
    track.add_clip(0, Clip(asset=VideoAsset(id="m-1"), duration=5))
    timeline.add_track(track)
    assert "lut" not in timeline.to_json()["timeline"]

    timeline.lut = Lut(CUBE_URL)
    assert timeline.to_json()["timeline"]["lut"] == {"src": CUBE_URL, "intensity": 1.0}


def test_from_file_uploads_the_cube(tmp_path):
    cube = tmp_path / "teal-orange.cube"
    cube.write_text("LUT_3D_SIZE 2\n" + "0 0 0\n" * 8)
    connection = object()
    with mock.patch("videodb.editor.upload_bytes", return_value=CUBE_URL) as upload:
        lut = Lut.from_file(connection, str(cube), intensity=0.8)
    upload.assert_called_once_with(
        _connection=connection,
        content=cube.read_bytes(),
        name="teal-orange.cube",
        content_type="text/plain",
    )
    assert lut.to_json() == {"src": CUBE_URL, "intensity": 0.8}


def test_from_file_wraps_upload_errors(tmp_path):
    cube = tmp_path / "x.cube"
    cube.write_text("LUT_3D_SIZE 2\n")
    with mock.patch("videodb.editor.upload_bytes", side_effect=RuntimeError("boom")):
        with pytest.raises(InvalidRequestError, match="Failed to upload LUT"):
            Lut.from_file(object(), str(cube))
