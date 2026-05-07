import pytest
from unittest.mock import MagicMock
from videodb.collection import Collection
from videodb.video import Video

@pytest.fixture
def mock_connection():
    return MagicMock()

@pytest.fixture
def collection(mock_connection):
    return Collection(_connection=mock_connection, id="c-123", name="Test Collection")

def test_search_title_returns_video_list(collection, mock_connection):
    # Simulate the API response format
    mock_response = [
        {"video": {"id": "m-1", "name": "Video 1", "collection_id": "c-123"}},
        {"video": {"id": "m-2", "name": "Video 2", "collection_id": "c-123"}}
    ]
    mock_connection.post.return_value = mock_response

    # Call the method we fixed
    results = collection.search_title("test query")

    # Verification:
    # 1. Ensure it returns a list
    assert isinstance(results, list)
    assert len(results) == 2
    
    # 2. Ensure every item is a Video object (this is what we fixed!)
    assert all(isinstance(v, Video) for v in results)
    
    # 3. Verify the data was passed correctly to the Video constructor
    assert results[0].id == "m-1"
    assert results[1].name == "Video 2"

    # 4. Verify the API was called with correct parameters
    mock_connection.post.assert_called_once()
    args, kwargs = mock_connection.post.call_args
    assert "search/title" in kwargs["path"]
    assert kwargs["data"]["query"] == "test query"
