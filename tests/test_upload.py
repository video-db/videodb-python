from videodb._upload import upload


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


def test_upload_infers_url():
    conn = DummyConn()
    upload(conn, file_path="https://example.com/video.mp4")
    assert conn.data["url"] == "https://example.com/video.mp4"
