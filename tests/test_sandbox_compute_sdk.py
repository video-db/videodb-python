from collections import deque

import pytest

from videodb.audio import Audio
from videodb.client import Connection
from videodb.collection import Collection
from videodb.image import Image
from videodb.job import GenerationJob
from videodb.scene import Scene
from videodb.voice_clone import VoiceClone


class FakeConnection:
    def __init__(self, *, posts=None, job_responses=None):
        self.post_responses = deque(posts or [])
        self.job_responses = deque(job_responses or [])
        self.post_calls = []
        self.delete_calls = []

    def post(self, path, data=None, **kwargs):
        self.post_calls.append({"path": path, "data": data, "kwargs": kwargs})
        return self.post_responses.popleft()

    def delete(self, path, **kwargs):
        self.delete_calls.append({"path": path, "kwargs": kwargs})

    def get_job_status(self, job_id):
        return self.job_responses.popleft()


def test_generate_image_returns_async_job_with_sandbox_payload():
    connection = FakeConnection(
        posts=[
            {
                "job_id": "job-image",
                "status": "processing",
                "job_type": "image",
            }
        ]
    )
    collection = Collection(connection, id="collection-1")

    result = collection.generate_image(
        prompt="A red fox",
        model_name="black-forest-labs/FLUX.1-dev",
        config={"size": "1024x1024"},
        sandbox_id="bx-123",
    )

    assert isinstance(result, GenerationJob)
    assert result.job_id == "job-image"
    assert result.result_type == "image"
    assert connection.post_calls == [
        {
            "path": "collection/collection-1/generate/image",
            "data": {
                "prompt": "A red fox",
                "aspect_ratio": "1:1",
                "callback_url": None,
                "model_name": "black-forest-labs/FLUX.1-dev",
                "config": {"size": "1024x1024"},
                "sandbox_id": "bx-123",
            },
            "kwargs": {},
        }
    ]


def test_generate_voice_returns_async_job_with_clone_and_sandbox_payload():
    connection = FakeConnection(
        posts=[
            {
                "job_id": "job-voice",
                "status": "processing",
                "job_type": "tts",
            }
        ]
    )
    collection = Collection(connection, id="collection-1")

    result = collection.generate_voice(
        text="Hello",
        model_name="k2-fsa/OmniVoice",
        sandbox_id="bx-123",
        voice_clone_id="vc-123",
        config={"language": "English"},
    )

    assert isinstance(result, GenerationJob)
    assert result.job_id == "job-voice"
    assert result.result_type == "audio"
    assert connection.post_calls[0]["data"] == {
        "text": "Hello",
        "audio_type": "voice",
        "voice_name": "Default",
        "model_name": "k2-fsa/OmniVoice",
        "config": {"language": "English"},
        "callback_url": None,
        "sandbox_id": "bx-123",
        "voice_clone_id": "vc-123",
    }


def test_generate_voice_rejects_conflicting_clone_aliases():
    collection = Collection(FakeConnection(), id="collection-1")

    with pytest.raises(ValueError, match="cannot both be different"):
        collection.generate_voice(
            text="Hello",
            voice_clone_id="vc-one",
            clone_voice_id="vc-two",
        )


def test_generate_text_forwards_sandbox_fields_and_wait_mode():
    connection = FakeConnection(posts=[{"job_id": "job-text"}])
    collection = Collection(connection, id="collection-1")

    result = collection.generate_text(
        prompt="Summarize this",
        model_name="Qwen/Qwen3.5-9B",
        sandbox_id="bx-123",
        max_tokens=128,
        temperature=0.2,
        model_config={"top_p": 0.9},
        wait=False,
    )

    assert result == {"job_id": "job-text"}
    assert connection.post_calls == [
        {
            "path": "collection/collection-1/generate/text",
            "data": {
                "prompt": "Summarize this",
                "model_name": "Qwen/Qwen3.5-9B",
                "response_type": "text",
                "callback_url": None,
                "sandbox_id": "bx-123",
                "max_tokens": 128,
                "temperature": 0.2,
                "model_config": {"top_p": 0.9},
            },
            "kwargs": {"wait": False},
        }
    ]


@pytest.mark.parametrize(
    ("result_type", "asset_data", "asset_class"),
    [
        (
            "audio",
            {"id": "a-123", "collection_id": "collection-1"},
            Audio,
        ),
        (
            "image",
            {"id": "img-123", "collection_id": "collection-1"},
            Image,
        ),
    ],
)
def test_generation_job_wait_returns_typed_asset(
    result_type,
    asset_data,
    asset_class,
):
    connection = FakeConnection(
        job_responses=[
            {
                "success": True,
                "status": "done",
                "data": asset_data,
            }
        ]
    )
    job = GenerationJob(connection, "job-123", result_type=result_type)

    result = job.wait(timeout=10, interval=0)

    assert isinstance(result, asset_class)
    assert result.id == asset_data["id"]


def test_scene_describe_forwards_sandbox_id():
    connection = FakeConnection(posts=[{"description": "A person enters."}])
    scene = Scene(
        id="scene-1",
        video_id="video-1",
        start=0,
        end=5,
        description=None,
        connection=connection,
    )

    result = scene.describe(
        prompt="Describe the scene",
        model_name="Qwen/Qwen3.5-9B",
        model_config={"temperature": 0.1},
        sandbox_id="bx-123",
    )

    assert result == "A person enters."
    assert connection.post_calls[0] == {
        "path": "video/video-1/scene/scene-1/describe",
        "data": {
            "prompt": "Describe the scene",
            "model_name": "Qwen/Qwen3.5-9B",
            "model_config": {"temperature": 0.1},
            "sandbox_id": "bx-123",
        },
        "kwargs": {},
    }


def test_voice_clone_create_and_delete_routes():
    connection = FakeConnection(
        posts=[
            {
                "voice_clone_id": "vc-123",
                "ref_audio_id": "a-123",
                "name": "Narrator",
            }
        ]
    )

    voice_clone = Connection.create_voice_clone(
        connection,
        ref_audio_id="a-123",
        name="Narrator",
        collection_id="collection-1",
    )
    Connection.delete_voice_clone(connection, voice_clone.id)

    assert isinstance(voice_clone, VoiceClone)
    assert voice_clone.id == "vc-123"
    assert connection.delete_calls == [{"path": "voice_clone/vc-123", "kwargs": {}}]
