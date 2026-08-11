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
    - [Updating Video Metadata](#updating-video-metadata)
    - [Viewing and Streaming Videos](#viewing-and-streaming-videos)
    - [Understanding Videos](#understanding-videos)
    - [Creating Indexes](#creating-indexes)
    - [Retrieving Indexed Content](#retrieving-indexed-content)
    - [Working with Transcripts](#working-with-transcripts)
    - [Legacy Scene Extraction and Indexing](#legacy-scene-extraction-and-indexing)
    - [Adding Subtitles](#adding-subtitles)
    - [Generating Thumbnails](#generating-thumbnails)
- [Working with Collections](#working-with-collections)
    - [Audio and Image Management](#audio-and-image-management)
- [Advanced Features](#advanced-features)
    - [Realtime Video Editor](#realtime-video-editor)
    - [Real-Time Streams (RTStream)](#real-time-streams-rtstream)
    - [Capture Sessions (Desktop Recording)](#capture-sessions-desktop-recording)
    - [WebSocket Events](#websocket-events)
    - [Meeting Recording](#meeting-recording)
    - [Sandbox Compute](#sandbox-compute)
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

### Updating Video Metadata

```python
# Update video name
video.update(name="New Video Title")
```

### Viewing and Streaming Videos

```python
# Generate stream URL
stream_url = video.generate_stream()

# Play stream using VideoDB player
videodb.play_stream(stream_url)

# Play in browser/notebook
video.play()
```

### Understanding Videos

VideoDB 0.5 separates the retrieval pipeline into three primitives: **Understand → Index → Retrieve**. Understanding runs analyzers once and stores reusable, timestamped artifacts; indexing then decides how those artifacts can be retrieved.

```python
understanding = video.understand(
    analyzers=[
        {"type": "spoken_words", "name": "transcript"},
        {"type": "vlm", "name": "scene"},
    ]
)
understanding.wait_until_complete()

# Inspect analyzer status or output
for analyzer in understanding.list_analyzers():
    print(analyzer.name, analyzer.type, analyzer.status)

scene = understanding.get_analyzer("scene")
scene_output = scene.get_output()
```

Built-in analyzer types include `spoken_words`, `vlm`, `object_detection`, `ocr`, `brand_detection`, `activity_recognition`, and `location_detection`. An understanding run can be reopened with `video.get_understanding(id)`, listed with `video.list_understandings()`, or deleted independently of the video.

### Creating Indexes

Create one or more retrieval-ready indexes from the stored analyzer artifacts without analyzing the video again:

```python
from videodb import IndexCapability

transcript = understanding.get_analyzer("transcript")
scene = understanding.get_analyzer("scene")

transcript_index = video.index(
    source=transcript,
    name="transcript",
    use_for=[IndexCapability.semantic, IndexCapability.query],
)
scene_index = video.index(
    source=scene,
    name="scene",
    use_for=[
        IndexCapability.semantic,
        IndexCapability.query,
        IndexCapability.aggregate,
    ],
)

scene_index.wait_until_complete()
print(scene_index.status, scene_index.fields, scene_index.field_schema)
```

`use_for` declares whether an index supports semantic search, structured queries, and aggregation. The optional `fields` argument maps artifact fields into `semantic`, `filter`, `aggregate`, and `sort` groups; when omitted, VideoDB derives sensible groups from the artifact.

You can also index your own timestamped records:

```python
from videodb import FieldGroup

chapters = video.index(
    name="chapters",
    source=[
        {"start": 0.0, "end": 12.4, "summary": "Opening city skyline", "kind": "intro"},
        {"start": 12.4, "end": 45.0, "summary": "CEO discusses Q4 results", "kind": "presentation"},
    ],
    use_for=[IndexCapability.semantic, IndexCapability.query, IndexCapability.aggregate],
    fields={
        FieldGroup.semantic: ["summary"],
        FieldGroup.filter: ["kind"],
        FieldGroup.aggregate: ["kind"],
    },
)
```

Manage and inspect indexes through their manifests:

```python
indexes = video.list_indexes()
same_index = video.get_index(index_id=chapters.index_id)
page = same_index.records(limit=20)

same_index.delete()  # Deletes the index, not its video or understanding artifact
```

### Retrieving Indexed Content

Use high-level `search()` when VideoDB should plan across the available indexes, or choose a direct retrieval primitive when your application knows the operation:

```python
# Natural-language retrieval; VideoDB selects and combines indexes
response = video.search(
    query="someone discussing a product while holding a phone",
    top_k=10,
)
for shot in response:
    print(shot.start, shot.end, shot.generate_stream())

# Direct vector retrieval over selected semantic indexes
results = video.semantic_search(
    query="a presentation about financial results",
    index_names=["scene", "transcript"],
    top_k=10,
)

# Exact structured filtering over one index
results = video.query(
    index_name="chapters",
    filter=[{"field": "kind", "op": "==", "value": "presentation"}],
    limit=20,
)

# Counts and facets over one index
counts = video.aggregate(
    index_name="chapters",
    group_by="kind",
    metric="count",
)

# A grounded answer with optional timestamped sources
answer = video.ask(
    question="What financial results were discussed?",
    include_sources=True,
)
```

The same `search()`, `semantic_search()`, `query()`, `aggregate()`, and `ask()` methods are available on collections for retrieval across multiple videos. Existing applications can continue using `index_spoken_words()`, `index_scenes()`, and `legacy_search()` for legacy indexes.

### Working with Transcripts

```python
# Generate transcript
video.generate_transcript()

# Generate transcript with language hint
video.generate_transcript(language_code="en")

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

### Legacy Scene Extraction and Indexing

Extract and analyze scenes with the legacy indexing API. New applications should prefer `video.understand(...)` followed by `video.index(...)` as shown above:

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

# Describe individual scenes with custom model config
scenes = video.get_scene_index(scene_collection.scene_index_id)
scene = scenes[0]
scene.describe(
    prompt="Describe this scene",
    model_config={"model_name": "pro", "temperature": 0.5}
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

### Realtime Video Editor

Build multi-track video compositions programmatically using VideoDB's 4-layer architecture: **Assets** (raw media), **Clips** (how assets appear), **Tracks** (timeline lanes), and **Timeline** (final canvas).

**Example: Video with background music**

```python
from videodb import connect
from videodb.editor import Timeline, Track, Clip, VideoAsset, AudioAsset

conn = connect(api_key="YOUR_API_KEY")
video = conn.upload(url="https://www.youtube.com/watch?v=VIDEO_ID")
audio = conn.upload(file_path="./music.mp3")

# Create timeline
timeline = Timeline(conn)

# Video track
video_track = Track()
video_asset = VideoAsset(id=video.id, start=10)
video_clip = Clip(asset=video_asset, duration=30)
video_track.add_clip(0, video_clip)

# Audio track
audio_track = Track()
audio_asset = AudioAsset(id=audio.id, start=0, volume=0.3)
audio_clip = Clip(asset=audio_asset, duration=30)
audio_track.add_clip(0, audio_clip)

# Compose and render
timeline.add_track(video_track)
timeline.add_track(audio_track)
stream_url = timeline.generate_stream()
```

**Example: Export as an editable Premiere Pro project**

A timeline can be exported as an NLE bundle instead of a rendered video — the
cuts, text and captions as a Premiere project, plus the media the sequence
references. The work takes minutes, so `export()` returns immediately and the job
is polled.

```python
job = timeline.export(format="nle", name="My cut")

job.wait()                  # or poll job.refresh() yourself
if job.done:
    url = job.download_url()   # signed, minted per call — do not cache it
elif job.failed:
    print(job.error)           # wait() returns on failure too; check which
```

Not everything in a timeline has an equivalent in a project file — the bundle
includes a fidelity report (`fidelity.md`) saying what carried over and what
could not.

**Asset Types:**
- `VideoAsset` - Video clips with trim control (`start`, `volume`)
- `AudioAsset` - Background music, voiceovers, sound effects
- `ImageAsset` - Logos, watermarks, static overlays
- `TextAsset` - Custom text with typography (`Font`, `Background`, `Alignment`)
- `CaptionAsset` - Auto-generated subtitles synced to speech

**Clip Controls:**
- **Position & Scale**: `position=Position.topRight`, `scale=0.5`, `offset=Offset(x=0.1, y=-0.2)`
- **Visual Effects**: `opacity=0.8`, `fit=Fit.cover`, `filter=Filter.greyscale`
- **Transitions**: `transition=Transition(in_="fade", out="fade", duration=1)`

**Track Layering:**
- Clips on the same track play sequentially
- Clips on different tracks at the same time play simultaneously (overlays)

For advanced patterns (picture-in-picture, multi-audio layers, auto-captions), see the [Editor SDK documentation](https://docs.videodb.io/realtime-video-editor-sdk-44).

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

# Generate stream with player metadata
stream_url = rtstream.generate_stream(
    start=1711000000,
    end=1711003600,
    player_config={
        "title": "Live Feed",
        "description": "Stream recording",
        "slug": "live-feed"
    }
)

# Export a stopped stream as a video/audio asset
rtstream.stop()
export_result = rtstream.export(name="my_recording")

# List streams
streams = coll.list_rtstreams()
```

### Capture Sessions (Desktop Recording)

Record screen, microphone, and system audio from desktop applications using native capture binaries:

```bash
# Install capture dependencies
pip install 'videodb[capture]'
```

```python
from videodb.capture import CaptureClient

# Backend: Create a capture session
cap = coll.create_capture_session(
    end_user_id="user_abc",
    callback_url="https://example.com/webhook"
)

# Generate a client token for secure desktop auth
token = conn.generate_client_token(expires_in=86400)

# Desktop client: Start capture
client = CaptureClient(session_token=token)

# Request permissions
await client.request_permission("microphone")
await client.request_permission("screen")

# Configure channels and start recording
await client.start_capture_session(
    session_id=cap.id,
    channels=[
        {"type": "mic", "name": "mic:default"},
        {"type": "system_audio", "name": "system_audio:default"},
        {"type": "display", "name": "display:1"},
    ]
)

# Stop capture
await client.stop_capture_session()

# Get session details and export
cap = coll.get_capture_session(cap.id)
export_result = cap.export()

# List all capture sessions
sessions = coll.list_capture_sessions()
```

### WebSocket Events

Receive real-time transcript and indexing events via WebSocket:

```python
# Connect to WebSocket
ws = conn.connect_websocket()
await ws.connect()
print(f"Connection ID: {ws.connection_id}")

# Stream events
async for event in ws.receive():
    print(event)

# Close connection
await ws.close()
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

### Sandbox Compute

Create dedicated compute for supported open-weight models:

```python
from videodb import SandboxTier

sandbox = conn.create_sandbox(
    tier=SandboxTier.small,
    name="my-sandbox",
    models=["rtdetr-v2-r50vd"],
)
sandbox.wait_for_ready(timeout=1200, interval=5)

# Retrieve or list existing sandboxes.
same_sandbox = conn.get_sandbox(sandbox.id)
active_sandboxes = conn.list_sandboxes(status="active")

# Keep the sandbox active while submitting inference work, then stop it.
sandbox.stop(grace=True)
sandbox.wait_for_stop(timeout=300, interval=5)
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

# Large prompts are uploaded automatically with a unique filename and
# sent as prompt_url instead of inline JSON to avoid request payload limits.
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
- **Timeline**: Multi-track video editor
- **SearchResult**: Search results with shots
- **Shot**: Time-segmented video clip
- **Understanding**: A reusable video analysis run containing analyzer artifacts
- **UnderstandingAnalyzer**: Status, output, and index-source handle for one analyzer
- **Index**: Retrieval-ready index manifest with status, capabilities, and schema
- **IndexRecord**: One timestamped record stored in an index
- **Scene**: Visual scene with frames
- **SceneCollection**: Collection of extracted scenes
- **Meeting**: Meeting recording session
- **RTStream**: Real-time stream processor
- **CaptureSession**: Desktop capture session with export
- **CaptureClient**: Native binary client for screen/audio recording
- **WebSocketConnection**: Real-time event streaming
- **Sandbox**: Dedicated compute for supported open-weight models
- **GenerationJob**: Asynchronous image or audio generation job
- **VoiceClone**: Reusable cloned-voice reference

### Constants and Enums

- `IndexCapability`: `semantic`, `query`, `aggregate`
- `FieldGroup`: `semantic`, `filter`, `aggregate`, `sort`
- `IndexType`: `spoken_word`, `scene` (legacy)
- `SearchType`: `semantic`, `keyword` (legacy)
- `SceneExtractionType`: `shot_based`, `time_based` (legacy)
- `Segmenter`: `word`, `sentence`, `time`
- `TranscodeMode`: `lightning`, `economy`
- `MediaType`: `video`, `audio`, `image`
- `SandboxTier`: `small`, `medium`
- `SandboxStatus`: `provisioning`, `active`, `alert`, `stopping`, `stopped`, `failed`

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
