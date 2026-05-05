import time
from typing import Optional

from videodb.audio import Audio
from videodb.image import Image
from videodb.exceptions import InvalidRequestError, RequestTimeoutError


class GenerationJob:
    """A self-inference generation job.

    OmniVoice text-to-speech and FLUX image generation return a VideoDB job
    after the initial server-side async task has dispatched work to
    inference-core. Use :meth:`wait` to poll until the final asset is ready.
    """

    def __init__(
        self,
        connection,
        job_id: str,
        output_url: Optional[str] = None,
        status: str = "processing",
        result_type: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> None:
        self._connection = connection
        self.id = job_id
        self.job_id = job_id
        self.output_url = output_url
        self.status = status or "processing"
        self.result_type = result_type
        self.data = data or {}

    def __repr__(self) -> str:
        return (
            f"GenerationJob("
            f"job_id={self.job_id}, "
            f"status={self.status}, "
            f"result_type={self.result_type})"
        )

    @classmethod
    def from_data(cls, connection, data: dict, result_type: Optional[str] = None):
        """Create a job from an API job payload."""
        data = data or {}
        job_id = data.get("job_id") or data.get("id")
        if not job_id:
            raise InvalidRequestError("Invalid generation job response: missing job_id")
        job_type = data.get("job_type")
        inferred_result_type = result_type
        if not inferred_result_type:
            if job_type == "tts":
                inferred_result_type = "audio"
            elif job_type == "image":
                inferred_result_type = "image"
        return cls(
            connection=connection,
            job_id=job_id,
            output_url=data.get("output_url"),
            status=data.get("status", "processing"),
            result_type=inferred_result_type,
            data=data,
        )

    def refresh(self):
        """Refresh this job's status from VideoDB."""
        job = self._connection.get_job_status(self.job_id)
        self.status = job.get("status", self.status)
        self.data = job.get("data") or {}
        self.output_url = self.data.get("output_url", self.output_url)
        if not self.result_type:
            job_type = self.data.get("job_type")
            if job_type == "tts":
                self.result_type = "audio"
            elif job_type == "image":
                self.result_type = "image"
        return self

    def wait(self, timeout: int = 600, interval: int = 5):
        """Poll this job until it completes and return the generated asset.

        :param int timeout: Maximum seconds to wait
        :param int interval: Seconds between polls
        :return: :class:`Audio <videodb.audio.Audio>`,
            :class:`Image <videodb.image.Image>`, or final job data if the
            result type cannot be inferred
        """
        deadline = time.time() + timeout
        while True:
            self.refresh()
            if self.status != "processing":
                break
            if time.time() >= deadline:
                raise RequestTimeoutError(
                    f"Generation job {self.job_id} did not complete within {timeout} seconds"
                )
            time.sleep(interval)

        if self.status == "failed":
            raise InvalidRequestError(f"Generation job {self.job_id} failed")

        return self._to_asset()

    def _to_asset(self):
        data = self.data or {}
        asset_id = data.get("id")
        if self.result_type == "audio" or (asset_id and asset_id.startswith("a-")):
            return Audio(self._connection, **data)
        if self.result_type == "image" or (asset_id and asset_id.startswith("img-")):
            return Image(self._connection, **data)
        return data
