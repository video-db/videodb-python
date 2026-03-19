import pytest
from videodb._utils._video import player_url_to_embed_url, build_iframe_embed_code


class TestPlayerUrlToEmbedUrl:
    """Tests for player_url_to_embed_url utility function."""

    def test_basic_conversion(self):
        """Test basic /watch to /embed conversion."""
        player_url = "https://player.videodb.io/watch?v=abc123"
        expected = "https://player.videodb.io/embed?v=abc123"
        assert player_url_to_embed_url(player_url) == expected

    def test_preserves_scheme_and_host(self):
        """Test that scheme and host are preserved."""
        player_url = "http://localhost:3000/watch?v=test-slug"
        expected = "http://localhost:3000/embed?v=test-slug"
        assert player_url_to_embed_url(player_url) == expected

    def test_strips_extra_query_params(self):
        """Test that only 'v' param is kept in embed URL."""
        player_url = "https://player.videodb.io/watch?v=abc123&other=param&foo=bar"
        expected = "https://player.videodb.io/embed?v=abc123"
        assert player_url_to_embed_url(player_url) == expected

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="player_url is required"):
            player_url_to_embed_url("")

    def test_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="player_url is required"):
            player_url_to_embed_url(None)

    def test_missing_v_param_raises_error(self):
        """Test that URL without 'v' param raises ValueError."""
        with pytest.raises(ValueError, match="must contain a 'v' query parameter"):
            player_url_to_embed_url("https://player.videodb.io/watch?other=param")


class TestBuildIframeEmbedCode:
    """Tests for build_iframe_embed_code utility function."""

    def test_basic_embed_code(self):
        """Test basic embed code generation."""
        player_url = "https://player.videodb.io/watch?v=abc123"
        result = build_iframe_embed_code(player_url)

        assert '<iframe src="https://player.videodb.io/embed?v=abc123"' in result
        assert 'width="100%"' in result
        assert 'height="405"' in result
        assert 'title="VideoDB Player"' in result
        assert 'frameborder="0"' in result
        assert "allowfullscreen" in result
        assert "</iframe>" in result

    def test_custom_dimensions(self):
        """Test custom width and height."""
        player_url = "https://player.videodb.io/watch?v=abc123"
        result = build_iframe_embed_code(player_url, width="800px", height=600)

        assert 'width="800px"' in result
        assert 'height="600"' in result

    def test_custom_title(self):
        """Test custom title attribute."""
        player_url = "https://player.videodb.io/watch?v=abc123"
        result = build_iframe_embed_code(player_url, title="My Custom Player")

        assert 'title="My Custom Player"' in result

    def test_fullscreen_disabled(self):
        """Test disabling fullscreen."""
        player_url = "https://player.videodb.io/watch?v=abc123"
        result = build_iframe_embed_code(player_url, allow_fullscreen=False)

        assert "allowfullscreen" not in result

    def test_fullscreen_enabled(self):
        """Test enabling fullscreen (default)."""
        player_url = "https://player.videodb.io/watch?v=abc123"
        result = build_iframe_embed_code(player_url, allow_fullscreen=True)

        assert "allowfullscreen" in result

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="player_url is required"):
            build_iframe_embed_code("")

    def test_none_url_raises_error(self):
        """Test that None URL raises ValueError."""
        with pytest.raises(ValueError, match="player_url is required"):
            build_iframe_embed_code(None)

    def test_zero_height_raises_error(self):
        """Test that zero height raises ValueError."""
        with pytest.raises(ValueError, match="height must be a positive integer"):
            build_iframe_embed_code("https://player.videodb.io/watch?v=abc", height=0)

    def test_negative_height_raises_error(self):
        """Test that negative height raises ValueError."""
        with pytest.raises(ValueError, match="height must be a positive integer"):
            build_iframe_embed_code("https://player.videodb.io/watch?v=abc", height=-100)

    def test_all_custom_params(self):
        """Test with all custom parameters."""
        player_url = "https://player.videodb.io/watch?v=my-video"
        result = build_iframe_embed_code(
            player_url,
            width="640px",
            height=480,
            title="Search Highlights",
            allow_fullscreen=True,
        )

        assert 'src="https://player.videodb.io/embed?v=my-video"' in result
        assert 'width="640px"' in result
        assert 'height="480"' in result
        assert 'title="Search Highlights"' in result
        assert "allowfullscreen" in result


class TestBuildIframeEmbedCodeIntegration:
    """Integration tests for build_iframe_embed_code with videodb module."""

    def test_import_from_videodb(self):
        """Test that build_iframe_embed_code can be imported from videodb."""
        from videodb import build_iframe_embed_code as imported_func

        assert imported_func is not None
        assert callable(imported_func)

    def test_usage_with_dict_response(self):
        """Test typical usage pattern with dict response (like CaptureSession.export)."""
        # Simulate a dict response from an API
        response = {
            "video_id": "v123",
            "player_url": "https://player.videodb.io/watch?v=exported-recording",
            "stream_url": "https://stream.videodb.io/abc.m3u8",
        }

        from videodb import build_iframe_embed_code

        embed_html = build_iframe_embed_code(response["player_url"])

        assert "embed?v=exported-recording" in embed_html
        assert "<iframe" in embed_html


class TestGetEmbedCodeMethods:
    """Tests for get_embed_code methods on SDK objects."""

    def test_rtstream_export_result_with_player_url(self):
        """Test RTStreamExportResult.get_embed_code when player_url exists."""
        from videodb.rtstream import RTStreamExportResult

        export_result = RTStreamExportResult(
            video_id="v123",
            player_url="https://player.videodb.io/watch?v=test-export",
        )
        iframe = export_result.get_embed_code()

        assert "embed?v=test-export" in iframe
        assert "<iframe" in iframe

    def test_rtstream_export_result_without_player_url_raises(self):
        """Test RTStreamExportResult.get_embed_code raises when player_url missing."""
        from videodb.rtstream import RTStreamExportResult

        export_result = RTStreamExportResult(video_id="v123", player_url=None)

        with pytest.raises(ValueError, match="player_url not available"):
            export_result.get_embed_code()
