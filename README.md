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

VideoDB Python SDK allows you to interact with the VideoDB serverless database. Manage videos as intelligent data, not files. It's scalable, cost-efficient & optimized for AI applications and LLM integration.

<!-- Documentation -->
<!-- ## Documentation
The documentation for the package can be found [here](https://videodb.io/) -->

<!-- Installation -->

## Installation

To install the package, run the following command in your terminal:

```
pip install videodb
```

<!-- USAGE EXAMPLES -->

## Quick Start

### Creating a Connection

Get an API key from the [VideoDB console](https://console.videodb.io). Free for first 50 uploads _(No credit card required)_.

```python
import videodb
conn = videodb.connect(api_key="YOUR_API_KEY")
```

## Working with a Single Video

---

### ⬆️ Uploading a Video

Now that you have established a connection to VideoDB, you can upload your videos using `conn.upload()`.
You can directly upload from `youtube`, `any public url`, `S3 bucket` or a `local file path`. A default collection is created when you create your first connection.

`upload` method returns a `Video` object.

```python
# Upload a video by url
video = conn.upload(url="https://www.youtube.com/watch?v=WDv4AWk0J3U")

# Upload a video from file system
video_f = conn.upload(file_path="./my_video.mp4")

```

### 📺 View your Video

Once uploaded, your video is immediately available for viewing in 720p resolution. ⚡️

- Generate a streamable url for the video using video.generate_stream()
- Preview the video using video.play(). This will open the video in your default browser/notebook

```python
video.generate_stream()
video.play()
```

### ⛓️ Stream Specific Sections of Videos

You can easily clip specific sections of a video by passing a timeline of the start and end timestamps (in seconds) as a parameter.
For example, this will generate and play a compilation of the first `10 seconds` and the clip between the `120th` and the `140th` second.

```python
stream_link = video.generate_stream(timeline=[[0,10], [120,140]])
play_stream(stream_link)
```

### 🔍 Search Inside a Video

To search bits inside a video, you have to `index` the video first. This can be done by a simple command.
_P.S. Indexing may take some time for longer videos._

```python
video.index_spoken_words()
result = video.search("Morning Sunlight")
result.play()
video.get_transcript()
```

`Videodb` is launching more indexing options in upcoming versions. As of now you can try the `semantic` index - Index by spoken words.

In the future you'll be able to index videos using:

1. **Scene** - Visual concepts and events.
2. **Faces**.
3. **Specific domain Index** like Football, Baseball, Drone footage, Cricket etc.

### Viewing Search Results

`video.search()` returns a `SearchResults` object, which contains the sections or as we call them, `shots` of videos which semantically match your search query.

- `result.get_shots()` Returns a list of Shot(s) that matched the search query.
- `result.play()` Returns a playable url for the video (similar to video.play(); you can open this link in the browser, or embed it into your website using an iframe).

## RAG: Search inside Multiple Videos

---

`VideoDB` can store and search inside multiple videos with ease. By default, videos are uploaded to your default collection.

### 🔄 Using Collection to Upload Multiple Videos

```python
# Get the default collection
coll = conn.get_collection()

# Upload Videos to a collection
coll.upload(url="https://www.youtube.com/watch?v=lsODSDmY4CY")
coll.upload(url="https://www.youtube.com/watch?v=vZ4kOr38JhY")
coll.upload(url="https://www.youtube.com/watch?v=uak_dXHh6s4")
```

- `conn.get_collection()` : Returns a Collection object; the default collection.
- `coll.get_videos()` : Returns a list of Video objects; all videos in the collections.
- `coll.get_video(video_id)`: Returns a Video object, corresponding video from the provided `video_id`.
- `coll.delete_video(video_id)`: Deletes the video from the Collection.

### 📂 Search Inside Collection

You can simply Index all the videos in a collection and use the search method to find relevant results.
Here we are indexing the spoken content of a collection and performing semantic search.

```python
# Index all videos in collection
for video in coll.get_videos():
    video.index_spoken_words()

# search in the collection of videos
results = coll.search(query = "What is Dopamine?")
results.play()
```

The result here has all the matching bits in a single stream from your collection. You can use these results in your application right away.

### 🌟 Explore the Video object

There are multiple methods available on a Video Object, that can be helpful for your use-case.

**Get the Transcript**

```python
# words with timestamps
text_json = video.get_transcript()
text = video.get_transcript_text()
print(text)
```

**Add Subtitles to a video**

It returns a new stream instantly with subtitles added to the video.

```python
new_stream = video.add_subtitle()
play_stream(new_stream)
```

**Get Thumbnail of a Video:**

`video.generate_thumbnail()`: Returns a thumbnail image of video.

**Delete a video:**

`video.delete()`: Deletes the video.

Checkout more examples and tutorials 👉 [Build with VideoDB](https://docs.videodb.io/build-with-videodb-35) to explore what you can build with `VideoDB`.

---

<!-- ROADMAP -->

## Roadmap

- Adding More Indexes : `Face`, `Scene`, `Security`, `Events`, and `Sports`
- Give prompt support to generate thumbnails using GenAI.
- Give prompt support to access content.
- Give prompt support to edit videos.
- See the [open issues](https://github.com/video-db/videodb-python/issues) for a list of proposed features (and known issues).

---

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[pypi-shield]: https://img.shields.io/pypi/v/videodb?style=for-the-badge
[pypi-url]: https://pypi.org/project/videodb/
[python-shield]: https://img.shields.io/pypi/pyversions/videodb?style=for-the-badge
[stars-shield]: https://img.shields.io/github/stars/video-db/videodb-python.svg?style=for-the-badge
[stars-url]: https://github.com/video-db/videodb-python/stargazers
[issues-shield]: https://img.shields.io/github/issues/video-db/videodb-python.svg?style=for-the-badge
[issues-url]: https://github.com/video-db/videodb-python/issues
[website-shield]: https://img.shields.io/website?url=https%3A%2F%2Fvideodb.io%2F&style=for-the-badge&label=videodb.io
[website-url]: https://videodb.io/
