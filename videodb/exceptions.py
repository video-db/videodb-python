"""videodb.exceptions

This module contains the set of Videodb's exceptions.
"""


class VideodbError(Exception):
    """
    Base class for all videodb exceptions.
    """

    def __init__(self, message: str = "An error occurred", cause=None):
        super(VideodbError, self).__init__(message)
        self.cause = cause

    def __str__(self):
        return f"{super(VideodbError, self).__str__()} {'caused by ' + str(self.cause) if self.cause else ''}"


class AuthenticationError(VideodbError):
    """
    Raised when authentication is required or failed.
    """

    def __init__(self, message, response=None):
        super(AuthenticationError, self).__init__(message)
        self.response = response


class InvalidRequestError(VideodbError):
    """
    Raised when a request is invalid.
    """

    def __init__(self, message, response=None):
        super(InvalidRequestError, self).__init__(message)
        self.response = response


class RequestTimeoutError(VideodbError):
    """
    Raised when a request times out.
    """

    def __init__(self, message, response=None):
        super(RequestTimeoutError, self).__init__(message)
        self.response = response


class SearchError(VideodbError):
    """
    Raised when a search is invalid.
    """

    def __init__(self, message):
        super(SearchError, self).__init__(message)
