from videodb._upload import upload, VideodbError
from videodb._constants import MediaType


class DummyConn:
    def __init__(self):
        self.collection_id = "default"
        self.data = None

    def get(self, path, params=None, show_progress=False):
        # return fake upload url
        return {"upload_url": "http://upload"}

    def post(self, path, data=None, show_progress=False):
        self.data = data
        # mimic api returning id and url
        return {"id": "m-1", **(data or {})}


def test_upload_infers_url_from_source():
    conn = DummyConn()
    upload(conn, source="https://example.com/video.mp4")
    assert conn.data["url"] == "https://example.com/video.mp4"


def test_upload_source_conflict():
    conn = DummyConn()
    try:
        upload(conn, source="/tmp/file.mp4", file_path="/tmp/file.mp4")
    except VideodbError:
        assert True
    else:
        assert False, "Expected VideodbError"


def test_upload_media_type_positional():
    conn = DummyConn()
    upload(conn, "https://example.com/video.mp4", MediaType.video)
    assert conn.data["url"] == "https://example.com/video.mp4"
    assert conn.data["media_type"] == MediaType.video
