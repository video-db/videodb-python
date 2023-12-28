
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

  <h3 align="center">VideoDB Python Client</h3>

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
# VideoDB Python Client
The VideoDB Python client is a python package that allows you to interact with the VideoDB which is a serverless database that lets you manage video as intelligent data, not files. It is secure, scalable & optimized for AI- applications and LLM integrations.

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
To create a new connection you need to get API key from [VideoDB console](https://console.videodb.io). You can directly upload from youtube, any public url, S3 bucket or local file path. A default collection is created when you create a new connection.

```python
import videodb

# create a new connection to the VideoDB
conn = videodb.connect(api_key="YOUR_API_KEY")

# upload to the default collection using the video url returns a Video object
video = conn.upload(url="https://www.youtube.com/")

# upload to the default collection using the local file path returns a Video object
video = conn.upload(file_path="path/to/video.mp4")

# get the stream url for the video
stream_url = video.generate_stream()

```

### Getting a Collection
To get a collection, use the `get_collection` method on the established database connection object. This method returns a `Collection` object.

```python
import videodb

# create a connection to the VideoDB
conn = videodb.connect(api_key="YOUR_API_KEY")

# get the default collection
collection = conn.get_collection()

# Upload a video to the collection returns a Video object
video = collection.upload(url="https://www.youtube.com/")

# async upload
collection.upload(url="https://www.youtube.com/", callback_url="https://yourdomain.com/callback")

# get all the videos in the collection returns a list of Video objects
videos = collection.get_videos()

# get a video from the collection returns a Video object
video = collection.get_video("video_id")

# delete the video from the collection
collection.delete_video("video_id")

```

### Multi Modal Indexing

#### Spoken words indexing
```python
import videodb

# create a connection to the VideoDB and get the default collection
conn = videodb.connect(api_key="YOUR_API_KEY")
collection = conn.get_collection()

# get the video from the collection
video = collection.get_video("video_id")

# index the video for semantic search
video.index_spoken_words()

# search relevant moment in video and stream resultant video clip instantly.
# returns a SearchResults object
# for searching the video, the video must be indexed please use index_spoken_words() before searching
# optional parameters:
#   - type: Optional[str] to specify the type of search. default is "semantic"
#   - result_threshold: Optional[int] to specify the number of results to return. default is 5
#   - score_threshold: Optional[float] to specify the score threshold for the results. default is 0.2
result = video.search("what is videodb?")
# get stream url of the result
stream_url = result.compile()
# get shots of the result returns a list of Shot objects
shots = result.get_shots()
# get stream url of the shot
short_stream_url = shots[0].compile()

# search relevant moment in collections and stream resultant video clip instantly.
# returns a SearchResults object
result = collection.search("what is videodb?")
# get stream url of the result
stream_url = result.compile()
# get shots of the result returns a list of Shot objects
shots = result.get_shots()
# get stream url of the shot
short_stream_url = shots[0].generate_stream()

```

### Video Object Methods
```python
import videodb

# create a connection to the VideoDB, get the default collection and get a video
conn = videodb.connect(api_key="YOUR_API_KEY")
collection = conn.get_collection()
video = collection.get_video("video_id")

# get the stream url of the dynamically curated video based on the given timeline sequence
# optional parameters:
#   - timeline: Optional[list[tuple[int, int]] to specify the start and end time of the video
stream_url = video.generate_stream(timeline=[(0, 10), (30, 40)])

# get thumbnail url of the video
thumbnail_url = video.generate_thumbnail()

# get transcript of the video
# optional parameters:
#  - force: Optional[bool] to force get the transcript. default is False
transcript = video.get_transcript()

# get transcript text of the video
# optional parameters:
#  - force: Optional[bool] to force get the transcript text. default is False
transcript_text = video.get_transcript_text()

# add subtitle to the video and get the stream url of the video with subtitle
stream_url = video.add_subtitle()

# delete the video from the collection
video.delete()

```

<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/video-db/videodb-python/issues) for a list of proposed features (and known issues).


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[pypi-shield]: https://img.shields.io/pypi/v/videodb?style=for-the-badge
[pypi-url]: https://pypi.org/project/videodb/
[python-shield]:https://img.shields.io/pypi/pyversions/videodb?style=for-the-badge
[stars-shield]: https://img.shields.io/github/stars/video-db/videodb-python.svg?style=for-the-badge
[stars-url]: https://github.com/video-db/videodb-python/stargazers
[issues-shield]: https://img.shields.io/github/issues/video-db/videodb-python.svg?style=for-the-badge
[issues-url]: https://github.com/video-db/videodb-python/issues
[website-shield]: https://img.shields.io/website?url=https%3A%2F%2Fvideodb.io%2F&style=for-the-badge&label=videodb.io
[website-url]: https://videodb.io/
