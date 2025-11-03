<!-- PROJECT SHIELDS -->
<!--
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![PyPI version][pypi-shield]][pypi-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Website][website-shield]][website-url]

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://videodb.io/">
    <img src="https://codaio.imgix.net/docs/_s5lUnUCIU/blobs/bl-RgjcFrrJjj/d3cbc44f8584ecd42f2a97d981a144dce6a66d83ddd5864f723b7808c7d1dfbc25034f2f25e1b2188e78f78f37bcb79d3c34ca937cbb08ca8b3da1526c29da9a897ab38eb39d084fd715028b7cc60eb595c68ecfa6fa0bb125ec2b09da65664a4f172c2f" alt="Logo" width="300" height="">
  </a>

  <h3 align="center">VideoDB Python SDK</h3>

  <p align="center">
    Video Database for your AI Applications
    <br />
    <a href="https://docs.videodb.io"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/video-db/videodb-cookbook">View Demo</a>
    ·
    <a href="https://github.com/video-db/videodb-python/issues">Report Bug</a>
    ·
    <a href="https://github.com/video-db/videodb-python/issues">Request Feature</a>
  </p>
</p>

<!-- ABOUT THE PROJECT -->

# VideoDB Python SDK

VideoDB Python SDK provides programmatic access to VideoDB's serverless video infrastructure. Build AI applications that understand and process video as structured data with support for semantic search, scene extraction, transcript generation, and multimodal content generation.

## 📑 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
    - [Establishing a Connection](#establishing-a-connection)
    - [Uploading Media](#uploading-media)
    - [Viewing and Streaming Videos](#viewing-and-streaming-videos)
    - [Searching Inside Videos](#searching-inside-videos)
    - [Working with Transcripts](#working-with-transcripts)
    - [Scene Extraction and Indexing](#scene-extraction-and-indexing)
    - [Adding Subtitles](#adding-subtitles)
    - [Generating Thumbnails](#generating-thumbnails)
- [Working with Collections](#working-with-collections)
    - [Audio and Image Management](#audio-and-image-management)
- [Advanced Features](#advanced-features)
    - [Timeline Builder](#timeline-builder)
    - [Real-Time Streams (RTStream)](#real-time-streams-rtstream)
    - [Meeting Recording](#meeting-recording)
    - [Generative Media](#generative-media)
    - [Video Dubbing and Translation](#video-dubbing-and-translation)
    - [Transcoding](#transcoding)
    - [YouTube Integration](#youtube-integration)
    - [Billing and Usage](#billing-and-usage)
    - [Download Streams](#download-streams)
- [Configuration Options](#configuration-options)
    - [Subtitle Customization](#subtitle-customization)
    - [Text Overlay Styling](#text-overlay-styling)
- [Error Handling](#error-handling)
- [API Reference](#api-reference)
- [Examples and Tutorials](#examples-and-tutorials)
- [Contributing](#contributing)
- [Resources](#resources)
- [License](#license)

## Installation

```bash
pip install videodb
```

**Requirements:**
- Python 3.8 or higher
- Dependencies: `requests>=2.25.1`, `backoff>=2.2.1`, `tqdm>=4.66.1`

## Quick Start

### Establishing a Connection

Get your API key from [VideoDB Console](https://console.videodb.io). Free for first 50 uploads (no credit card required).

```python
import videodb

# Connect using API key
conn = videodb.connect(api_key="YOUR_API_KEY")

# Or set environment variable VIDEO_DB_API_KEY
# conn = videodb.connect()
```

### Uploading Media

Upload videos, audio files, or images from various sources:

```python
# Upload video from YouTube URL
video = conn.upload(url="https://www.youtube.com/watch?v=VIDEO_ID")

# Upload from public URL
video = conn.upload(url="https://example.com/video.mp4")

# Upload from local file
video = conn.upload(file_path="./my_video.mp4")

# Upload with metadata
video = conn.upload(
    file_path="./video.mp4",
    name="My Video",
    description="Video description"
)
```

The `upload()` method returns `Video`, `Audio`, or `Image` objects based on the media type.

### Viewing and Streaming Videos

```python
# Generate stream URL
stream_url = video.generate_stream()

# Play in browser/notebook
video.play()

# Stream specific sections (timestamps in seconds)
stream_url = video.generate_stream(timeline=[[0, 10], [120, 140]])
videodb.play_stream(stream_url)
```

### Searching Inside Videos

Index and search video content semantically:

```python
from videodb import SearchType, IndexType

# Index spoken words for semantic search
video.index_spoken_words()

# Search for content
results = video.search("morning sunlight")

# Access search results
shots = results.get_shots()
for shot in shots:
    print(f"Found at {shot.start}s - {shot.end}s: {shot.text}")

# Play compiled results
results.play()
```

**Search Types:**
- `SearchType.semantic` - Semantic search (default)
- `SearchType.keyword` - Keyword-based search  
- `SearchType.scene` - Visual scene search

### Working with Transcripts

```python
# Generate transcript
video.generate_transcript()

# Get transcript with timestamps
transcript = video.get_transcript()

# Get plain text transcript
text = video.get_transcript_text()

# Get transcript for specific time range
transcript = video.get_transcript(start=10, end=60)

# Translate transcript
translated = video.translate_transcript(
    language="Spanish",
    additional_notes="Formal tone"
)
```

**Segmentation Options:**
- `videodb.Segmenter.word` - Word-level timestamps
- `videodb.Segmenter.sentence` - Sentence-level timestamps
- `videodb.Segmenter.time` - Time-based segments

### Scene Extraction and Indexing

Extract and analyze scenes from videos:

```python
from videodb import SceneExtractionType

# Extract scenes using shot detection
scene_collection = video.extract_scenes(
    extraction_type=SceneExtractionType.shot_based,
    extraction_config={"threshold": 20, "frame_count": 1}
)

# Extract scenes at time intervals
scene_collection = video.extract_scenes(
    extraction_type=SceneExtractionType.time_based,
    extraction_config={
        "time": 10,
        "frame_count": 1,
        "select_frames": ["first"]
    }
)

# Index scenes for semantic search
scene_index_id = video.index_scenes(
    extraction_type=SceneExtractionType.shot_based,
    prompt="Describe the visual content of this scene"
)

# Search within scenes
results = video.search(
    query="outdoor landscape",
    search_type=SearchType.scene,
    index_type=IndexType.scene
)

# List scene indexes
scene_indexes = video.list_scene_index()

# Get specific scene index
scenes = video.get_scene_index(scene_index_id)

# Delete scene collection
video.delete_scene_collection(scene_collection.id)
```

### Adding Subtitles

```python
from videodb import SubtitleStyle

# Add subtitles with default style
stream_url = video.add_subtitle()

# Customize subtitle appearance
style = SubtitleStyle(
    font_name="Arial",
    font_size=24,
    primary_colour="&H00FFFFFF",
    bold=True
)
stream_url = video.add_subtitle(style=style)
```

### Generating Thumbnails

```python
# Get default thumbnail
thumbnail_url = video.generate_thumbnail()

# Generate thumbnail at specific timestamp
thumbnail_image = video.generate_thumbnail(time=30.5)

# Get all thumbnails
thumbnails = video.get_thumbnails()
```

## Working with Collections

Organize and search across multiple videos:

```python
# Get default collection
coll = conn.get_collection()

# Create new collection
coll = conn.create_collection(
    name="My Collection",
    description="Collection description",
    is_public=False
)

# List all collections
collections = conn.get_collections()

# Update collection
coll = conn.update_collection(
    id="collection_id",
    name="Updated Name",
    description="Updated description"
)

# Upload to collection
video = coll.upload(url="https://example.com/video.mp4")

# Get videos in collection
videos = coll.get_videos()
video = coll.get_video(video_id)

# Search across collection
results = coll.search(query="specific content")

# Search by title
results = coll.search_title("video title")

# Make collection public/private
coll.make_public()
coll.make_private()

# Delete collection
coll.delete()
```

### Audio and Image Management

```python
# Get audio files
audios = coll.get_audios()
audio = coll.get_audio(audio_id)

# Generate audio URL
audio_url = audio.generate_url()

# Get images
images = coll.get_images()
image = coll.get_image(image_id)

# Generate image URL
image_url = image.generate_url()

# Delete media
audio.delete()
image.delete()
```

## Advanced Features

### Timeline Builder

Create custom video compilations programmatically:

```python
from videodb.timeline import Timeline
from videodb.asset import VideoAsset, AudioAsset, ImageAsset, TextAsset
from videodb import TextStyle

timeline = Timeline(conn)

# Add video clips
video_asset = VideoAsset(asset_id=video.id, start=0, end=30)
timeline.add_inline(video_asset)

# Add audio overlay
audio_asset = AudioAsset(
    asset_id=audio.id,
    start=0,
    end=10,
    fade_in_duration=2,
    fade_out_duration=2
)
timeline.add_overlay(start=0, asset=audio_asset)

# Add image overlay
image_asset = ImageAsset(
    asset_id=image.id,
    width=200,
    height=200,
    x=10,
    y=10,
    duration=5
)
timeline.add_overlay(start=5, asset=image_asset)

# Add text overlay
text_style = TextStyle(fontsize=24, fontcolor="white")
text_asset = TextAsset(text="Hello World", duration=3, style=text_style)
timeline.add_overlay(start=0, asset=text_asset)

# Generate compiled stream
stream_url = timeline.generate_stream()
```

### Real-Time Streams (RTStream)

Process live video streams in real-time:

```python
from videodb import SceneExtractionType

# Connect to real-time stream
rtstream = coll.connect_rtstream(
    url="rtsp://example.com/stream",
    name="Live Stream"
)

# Start or Stop processing
rtstream.stop()
rtstream.start()

# Index scenes from stream
scene_index = rtstream.index_scenes(
    extraction_type=SceneExtractionType.time_based,
    extraction_config={"time": 2, "frame_count": 5},
    prompt="Describe the scene"
)

# Start or Stop scene indexing
scene_index.stop()
scene_index.start()

# Get scenes
scenes = scene_index.get_scenes(page=1, page_size=100)

# Create alerts for events
alert_id = scene_index.create_alert(
    event_id=event_id,
    callback_url="https://example.com/callback"
)

# Enable/disable alerts

scene_index.disable_alert(alert_id)
scene_index.enable_alert(alert_id)


# List streams
streams = coll.list_rtstreams()
```

### Meeting Recording

Record and process virtual meetings:

```python
# Start meeting recording
meeting = conn.record_meeting(
    meeting_url="https://meet.google.com/xxx-yyyy-zzz",
    bot_name="Recorder Bot",
    meeting_title="Team Meeting",
    callback_url="https://example.com/callback"
)

# Check meeting status
meeting.refresh()
print(meeting.status)  # initializing, processing, or done

# Wait for completion
meeting.wait_for_status("done", timeout=14400, interval=120)

# Get meeting details
if meeting.is_completed:
    video_id = meeting.video_id
    video = coll.get_video(video_id)
    
# Get meeting from video
meeting_info = video.get_meeting()
```

### Generative Media

Generate images, audio, and videos using AI:

```python
# Generate image
image = coll.generate_image(
    prompt="A beautiful sunset over mountains",
    aspect_ratio="16:9"
)

# Generate music
audio = coll.generate_music(
    prompt="Upbeat electronic music",
    duration=30
)

# Generate sound effects
audio = coll.generate_sound_effect(
    prompt="Door closing sound",
    duration=2
)

# Generate voice from text
audio = coll.generate_voice(
    text="Hello, welcome to VideoDB",
    voice_name="Default"
)

# Generate video
video = coll.generate_video(
    prompt="A cat playing with a ball",
    duration=5
)

# Generate text using LLM
response = coll.generate_text(
    prompt="Summarize this content",
    model_name="pro",  # basic, pro, or ultra
    response_type="text"  # text or json
)
```

### Video Dubbing and Translation

```python
# Dub video to another language
dubbed_video = coll.dub_video(
    video_id=video.id,
    language_code="es",
    callback_url="https://example.com/callback"
)
```

### Transcoding

```python
from videodb import TranscodeMode, VideoConfig, AudioConfig

# Start transcoding job
job_id = conn.transcode(
    source="https://example.com/video.mp4",
    callback_url="https://example.com/callback",
    mode=TranscodeMode.economy,
    video_config=VideoConfig(resolution=1080, quality=23),
    audio_config=AudioConfig(mute=False)
)

# Check transcode status
status = conn.get_transcode_details(job_id)
```

### YouTube Integration

```python
# Search YouTube
results = conn.youtube_search(
    query="machine learning tutorial",
    result_threshold=10,
    duration="medium"
)

for result in results:
    print(result["title"], result["url"])
```

### Billing and Usage

```python
# Check usage
usage = conn.check_usage()

# Get invoices
invoices = conn.get_invoices()
```

### Download Streams

```python
# Download compiled stream
download_info = conn.download(
    stream_link="https://stream.videodb.io/...",
    name="my_compilation"
)
```

## Configuration Options

### Subtitle Customization

```python
from videodb import SubtitleStyle, SubtitleAlignment, SubtitleBorderStyle

style = SubtitleStyle(
    font_name="Arial",
    font_size=18,
    primary_colour="&H00FFFFFF",      # White
    secondary_colour="&H000000FF",     # Blue
    outline_colour="&H00000000",       # Black
    back_colour="&H00000000",          # Black
    bold=False,
    italic=False,
    underline=False,
    strike_out=False,
    scale_x=1.0,
    scale_y=1.0,
    spacing=0,
    angle=0,
    border_style=SubtitleBorderStyle.outline,
    outline=1.0,
    shadow=0.0,
    alignment=SubtitleAlignment.bottom_center,
    margin_l=10,
    margin_r=10,
    margin_v=10
)
```

### Text Overlay Styling

```python
from videodb import TextStyle

style = TextStyle(
    fontsize=24,
    fontcolor="black",
    font="Sans",
    box=True,
    boxcolor="white",
    boxborderw="10"
)
```

## Error Handling

```python
from videodb.exceptions import (
    VideodbError,
    AuthenticationError,
    InvalidRequestError,
    SearchError
)

try:
    conn = videodb.connect(api_key="invalid_key")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")

try:
    video = conn.upload(url="invalid_url")
except InvalidRequestError as e:
    print(f"Invalid request: {e}")

try:
    results = video.search("query")
except SearchError as e:
    print(f"Search error: {e}")
```

## API Reference

### Core Objects

- **Connection**: Main client for API interaction
- **Collection**: Container for organizing media
- **Video**: Video file with processing methods
- **Audio**: Audio file representation
- **Image**: Image file representation
- **Timeline**: Video compilation builder
- **SearchResult**: Search results with shots
- **Shot**: Time-segmented video clip
- **Scene**: Visual scene with frames
- **SceneCollection**: Collection of extracted scenes
- **Meeting**: Meeting recording session
- **RTStream**: Real-time stream processor

### Constants and Enums

- `IndexType`: `spoken_word`, `scene`
- `SearchType`: `semantic`, `keyword`, `scene`
- `SceneExtractionType`: `shot_based`, `time_based`
- `Segmenter`: `word`, `sentence`, `time`
- `TranscodeMode`: `lightning`, `economy`
- `MediaType`: `video`, `audio`, `image`

For detailed API documentation, visit [docs.videodb.io](https://docs.videodb.io).

## Examples and Tutorials

Explore practical examples and use cases in the [VideoDB Cookbook](https://github.com/video-db/videodb-cookbook):

- Semantic video search
- Scene-based indexing and retrieval
- Custom video compilations
- Meeting transcription and analysis
- Real-time stream processing
- Multi-language video dubbing

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Resources

- **Documentation**: [docs.videodb.io](https://docs.videodb.io)
- **Console**: [console.videodb.io](https://console.videodb.io)
- **Examples**: [github.com/video-db/videodb-cookbook](https://github.com/video-db/videodb-cookbook)
- **Community**: [Discord](https://discord.gg/py9P639jGz)
- **Issues**: [GitHub Issues](https://github.com/video-db/videodb-python/issues)

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

---

<!-- MARKDOWN LINKS & IMAGES -->

[pypi-shield]: https://img.shields.io/pypi/v/videodb?style=for-the-badge
[pypi-url]: https://pypi.org/project/videodb/
[python-shield]: https://img.shields.io/pypi/pyversions/videodb?style=for-the-badge
[stars-shield]: https://img.shields.io/github/stars/video-db/videodb-python.svg?style=for-the-badge
[stars-url]: https://github.com/video-db/videodb-python/stargazers
[issues-shield]: https://img.shields.io/github/issues/video-db/videodb-python.svg?style=for-the-badge
[issues-url]: https://github.com/video-db/videodb-python/issues
[website-shield]: https://img.shields.io/website?url=https%3A%2F%2Fvideodb.io%2F&style=for-the-badge&label=videodb.io
[website-url]: https://videodb.io/
