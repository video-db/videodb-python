"""Http client Module."""

import logging
import requests

from tqdm import tqdm
from typing import (
    Callable,
    Optional,
)
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from videodb._constants import (
    HttpClientDefaultValues,
    Status,
)
from videodb._utils._poll import PollSchedule, retry_after_from
from videodb.exceptions import (
    AuthenticationError,
    InvalidRequestError,
)

logger = logging.getLogger(__name__)


class HttpClient:
    """Http client for making requests"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        version: str,
        max_retries: Optional[int] = HttpClientDefaultValues.max_retries,
        **kwargs,
    ) -> None:
        """Create a new http client instance

        :param str api_key: The api key to use for authentication
        :param str base_url: The base url to use for the api
        :param int max_retries: (optional) The maximum number of retries to make for a request
        """
        self.session = requests.Session()

        retries = Retry(
            total=max_retries,
            backoff_factor=HttpClientDefaultValues.backoff_factor,
            status_forcelist=HttpClientDefaultValues.status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.version = version
        kwargs = self._format_headers(kwargs)
        self.session.headers.update(
            {
                "x-access-token": api_key,
                "x-videodb-client": f"videodb-python/{self.version}",
                "Content-Type": "application/json",
                **kwargs,
            }
        )
        self.base_url = base_url
        logger.debug(f"Initialized http client with base url: {self.base_url}")

    def _make_request(
        self,
        method: Callable[..., requests.Response],
        path: str,
        base_url: Optional[str] = None,
        headers: Optional[dict] = None,
        wait: bool = True,
        show_progress: bool = False,
        poll_config: Optional[dict] = None,
        **kwargs,
    ):
        """Make a request to the api

        :param Callable method: The method to use for the request
        :param str path: The path to make the request to
        :param str base_url: (optional) The base url to use for the request
        :param dict headers: (optional) The headers to use for the request
        :param bool wait: If False, return raw data without polling (default True)
        :param bool show_progress: Show a progress bar while polling
        :param dict poll_config: Per-call ``PollSchedule`` overrides
        :param kwargs: The keyword arguments to pass to the request method
        :return: json response from the request
        """
        try:
            url = f"{base_url or self.base_url}/{path}"
            timeout = kwargs.pop("timeout", HttpClientDefaultValues.timeout)
            request_headers = {**self.session.headers, **(headers or {})}
            response = method(url, headers=request_headers, timeout=timeout, **kwargs)
            response.raise_for_status()
            if not wait:
                data = response.json().get("data")
                if data is not None:
                    return data
                return response.json()
            return self._parse_response(
                response, show_progress=show_progress, poll_config=poll_config
            )

        except requests.exceptions.RequestException as e:
            self._handle_request_error(e)

    def _handle_request_error(self, e: requests.exceptions.RequestException) -> None:
        """Handle request errors"""
        if isinstance(e, requests.exceptions.HTTPError):
            try:
                error_message = e.response.json().get("message", "Unknown error")
            except ValueError:
                error_message = e.response.text

            if e.response.status_code == 401:
                raise AuthenticationError(
                    f"Error: {error_message}", e.response
                ) from None
            else:
                raise InvalidRequestError(
                    f"Invalid request: {error_message}", e.response
                ) from None

        elif isinstance(e, requests.exceptions.RetryError):
            raise InvalidRequestError(
                "Invalid request: Max retries exceeded", e.response
            ) from None

        elif isinstance(e, requests.exceptions.Timeout):
            raise RequestTimeoutError(
                "Timeout error: Request timed out", e.response
            ) from None

        elif isinstance(e, requests.exceptions.ConnectionError):
            raise InvalidRequestError(
                "Invalid request: Connection error", e.response
            ) from None

        else:
            raise InvalidRequestError(
                f"Invalid request: {str(e)}", e.response
            ) from None

    def _get_output(
        self,
        url: str,
        show_progress: bool = False,
        poll_config: Optional[dict] = None,
        progress_bar=None,
    ):
        """Poll an output URL until the job completes or times out.

        Follows the server's ``retry_after`` hint when present, otherwise
        backs off locally.
        """
        schedule = PollSchedule(**(poll_config or {}))
        while True:
            response = self.session.get(url, timeout=HttpClientDefaultValues.timeout)
            response_json = response.json()
            status = response_json.get("status")
            if status not in (Status.in_progress, Status.processing):
                break

            percentage = response_json.get("data", {}).get("percentage")
            if percentage and show_progress and progress_bar:
                progress_bar.n = int(percentage)
                progress_bar.update(0)

            schedule.raise_if_expired(
                what="Job", output_url=url, last_response=response_json
            )
            hint = (
                response_json
                if retry_after_from(response_json) is not None
                else response
            )
            schedule.sleep(hint)

        if show_progress and progress_bar:
            progress_bar.n = 100
            progress_bar.update(0)
            progress_bar.close()
        return response_json.get("response") or response_json

    def _parse_response(
        self,
        response: requests.Response,
        show_progress: bool = False,
        poll_config: Optional[dict] = None,
    ):
        """Parse the response from the api"""
        try:
            response_json = response.json()
            if (
                response_json.get("status") == Status.processing
                and response_json.get("request_type", "sync") == "async"
            ):
                return None
            elif (
                response_json.get("status") == Status.processing
                and response_json.get("request_type", "sync") == "sync"
            ):
                progress_bar = None
                if show_progress:
                    progress_bar = tqdm(
                        total=100,
                        position=0,
                        leave=True,
                        bar_format="{l_bar}{bar:100}{r_bar}{bar:-100b}",
                    )
                response_json = self._get_output(
                    response_json.get("data", {}).get("output_url"),
                    show_progress=show_progress,
                    poll_config=poll_config,
                    progress_bar=progress_bar,
                )
                if response_json.get("success"):
                    return response_json.get("data")
                else:
                    raise InvalidRequestError(
                        f"Invalid request: {response_json.get('message')}", response
                    ) from None

            elif response_json.get("success"):
                return response_json.get("data")

            else:
                raise InvalidRequestError(
                    f"Invalid request: {response_json.get('message')}", response
                ) from None

        except ValueError:
            raise InvalidRequestError(
                f"Invalid request: {response.text}", response
            ) from None

    def _format_headers(self, headers: dict):
        """Format the headers"""
        formatted_headers = {}
        for key, value in headers.items():
            key = key.lower().replace("_", "-")
            formatted_headers[f"x-{key}"] = value
        return formatted_headers

    def _pop_poll_overrides(self, kwargs) -> dict:
        """Pull per-call poll overrides out of kwargs.

        Returned rather than stored on the client, so concurrent calls do
        not overwrite each other's cadence.
        """
        return {
            "max_poll_time": kwargs.pop("max_poll_time", None),
            "interval": kwargs.pop("poll_interval", None),
        }

    def get(
        self, path: str, show_progress: Optional[bool] = False, wait: bool = True, **kwargs
    ) -> requests.Response:
        """Make a get request"""
        poll_config = self._pop_poll_overrides(kwargs)
        return self._make_request(
            method=self.session.get,
            path=path,
            wait=wait,
            show_progress=show_progress,
            poll_config=poll_config,
            **kwargs,
        )

    def post(
        self, path: str, data=None, show_progress: Optional[bool] = False,
        wait: bool = True, **kwargs,
    ) -> requests.Response:
        """Make a post request"""
        poll_config = self._pop_poll_overrides(kwargs)
        return self._make_request(
            self.session.post,
            path,
            json=data,
            wait=wait,
            show_progress=show_progress,
            poll_config=poll_config,
            **kwargs,
        )

    def put(self, path: str, data=None, **kwargs) -> requests.Response:
        """Make a put request"""
        return self._make_request(self.session.put, path, json=data, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        """Make a delete request"""
        return self._make_request(self.session.delete, path, **kwargs)

    def patch(self, path: str, data=None, **kwargs) -> requests.Response:
        """Make a patch request"""
        return self._make_request(self.session.patch, path, json=data, **kwargs)
