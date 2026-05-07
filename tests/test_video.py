import pytest
from unittest.mock import MagicMock
from videodb.video import Video
from videodb.meeting import Meeting

@pytest.fixture
def mock_connection():
    return MagicMock()

@pytest.fixture
def video(mock_connection):
    return Video(_connection=mock_connection, id="m-123", collection_id="c-123")

def test_get_meeting_returns_meeting_object(video, mock_connection):
    # Simulate a successful meeting response
    mock_response = {
        "meeting_id": "meet-456",
        "status": "done",
        "meeting_url": "https://meet.google.com/abc"
    }
    mock_connection.get.return_value = mock_response

    # Call the method we hinted
    meeting = video.get_meeting()

    # Verification:
    assert isinstance(meeting, Meeting)
    assert meeting.id == "meet-456"
    assert meeting.collection_id == "c-123"

def test_get_meeting_returns_none_if_no_meeting(video, mock_connection):
    # Simulate no meeting found
    mock_connection.get.return_value = None

    meeting = video.get_meeting()

    assert meeting is None
