from typing import Dict, List, Union
from videodb._constants import (
    ApiPath,
    Segmenter,
)

_VALID_SEGMENTERS = {Segmenter.word, Segmenter.sentence, Segmenter.time}


class Audio:
    """Audio class to interact with the Audio

    :ivar str id: Unique identifier for the audio
    :ivar str collection_id: ID of the collection this audio belongs to
    :ivar str name: Name of the audio file
    :ivar float length: Duration of the audio in seconds
    :ivar list transcript: Timestamped transcript segments
    :ivar str transcript_text: Full transcript text
    """

    def __init__(
        self, _connection, id: str, collection_id: str, **kwargs
    ) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self.name = kwargs.get("name", None)
        self.length = kwargs.get("length", None)
        self.transcript = kwargs.get("transcript", None)
        self.transcript_text = kwargs.get("transcript_text", None)

    def __repr__(self) -> str:
        return (
            f"Audio("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"name={self.name}, "
            f"length={self.length})"
        )

    def generate_url(self) -> str:
        """Generate the signed url of the audio.

        :raises InvalidRequestError: If the get_url fails
        :return: The signed url of the audio
        :rtype: str
        """
        url_data = self._connection.post(
            path=f"{ApiPath.audio}/{self.id}/{ApiPath.generate_url}",
            params={"collection_id": self.collection_id},
        )
        return url_data.get("signed_url", None)

    def _fetch_transcript(
        self,
        start: int = None,
        end: int = None,
        segmenter: str = Segmenter.word,
        length: int = 1,
        force: bool = None,
    ) -> None:
        if segmenter not in _VALID_SEGMENTERS:
            raise ValueError(
                f"Invalid segmenter '{segmenter}'. "
                f"Must be one of: {', '.join(sorted(_VALID_SEGMENTERS))}"
            )
        if start is not None and start < 0:
            raise ValueError(f"start must be non-negative, got {start}")
        if end is not None and end < 0:
            raise ValueError(f"end must be non-negative, got {end}")
        if start is not None and end is not None and start > end:
            raise ValueError(
                f"start ({start}) must be less than or equal to end ({end})"
            )
        if self.transcript and not force and not start and not end:
            return
        transcript_data = self._connection.get(
            path=f"{ApiPath.audio}/{self.id}/{ApiPath.transcription}",
            params={
                "start": start,
                "end": end,
                "segmenter": segmenter,
                "length": length,
                "force": "true" if force else "false",
            },
            show_progress=True,
        )
        self.transcript = transcript_data.get("word_timestamps", [])
        self.transcript_text = transcript_data.get("text", "")

    def get_transcript(
        self,
        start: int = None,
        end: int = None,
        segmenter: Segmenter = Segmenter.word,
        length: int = 1,
        force: bool = None,
    ) -> List[Dict[str, Union[float, str]]]:
        """Get timestamped transcript segments for the audio.

        :param int start: Start time in seconds (must be >= 0 and <= end)
        :param int end: End time in seconds (must be >= 0 and >= start)
        :param Segmenter segmenter: How to split the transcript into segments.
            Must be one of :attr:`Segmenter.word` (default, one segment per word),
            :attr:`Segmenter.sentence` (one segment per sentence), or
            :attr:`Segmenter.time` (fixed-duration segments controlled by *length*)
        :param int length: Duration in seconds for each segment when
            *segmenter* is :attr:`Segmenter.time` (default 1)
        :param bool force: Force re-fetch transcript from the server,
            bypassing the local cache
        :raises ValueError: If *segmenter* is not a valid value, or if
            *start*/*end* are negative or *start* > *end*
        :return: List of dicts with keys: start (float), end (float), text (str)
        :rtype: List[Dict[str, Union[float, str]]]
        """
        self._fetch_transcript(
            start=start, end=end, segmenter=segmenter, length=length, force=force
        )
        return self.transcript

    def get_transcript_text(
        self,
        start: int = None,
        end: int = None,
    ) -> str:
        """Get plain text transcript for the audio.

        :param int start: Start time in seconds to get transcript from
        :param int end: End time in seconds to get transcript until
        :param bool force: Force fetch new transcript
        :return: Full transcript text as string
        :rtype: str
        """
        self._fetch_transcript(start=start, end=end)
        return self.transcript_text

    def generate_transcript(
        self,
        force: bool = None,
        language_code: str = None,
    ) -> dict:
        """Generate transcript for the audio.

        :param bool force: Force generate new transcript
        :param str language_code: Language code of the spoken audio. If not provided, language is automatically detected.
        :return: Success dict if transcript generated or already exists
        :rtype: dict
        """
        transcript_data = self._connection.post(
            path=f"{ApiPath.audio}/{self.id}/{ApiPath.transcription}",
            data={
                "force": True if force else False,
                "language_code": language_code,
            },
        )
        transcript = transcript_data.get("word_timestamps", [])
        if transcript:
            return {
                "success": True,
                "message": "Transcript generated successfully",
            }
        return transcript_data

    def delete(self) -> None:
        """Delete the audio.

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(f"{ApiPath.audio}/{self.id}")
