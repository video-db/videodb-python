from videodb.exceptions import (
    VideodbError,
    AuthenticationError,
    InvalidRequestError,
    SearchError,
)


def test_videodb_error():
    try:
        raise VideodbError("An error occurred", cause="Something")

    except VideodbError as e:
        assert str(e) == "An error occurred caused by Something"
        assert e.cause == "Something"


def test_authentication_error():
    try:
        raise AuthenticationError(
            "An error occurred with authentication", response="Something"
        )

    except AuthenticationError as e:
        print(e)
        assert str(e) == "An error occurred with authentication "
        assert e.response == "Something"


def test_invalid_request_error():
    try:
        raise InvalidRequestError(
            "An error occurred with request", response="Something"
        )

    except InvalidRequestError as e:
        assert str(e) == "An error occurred with request "
        assert e.response == "Something"


def test_search_error():
    try:
        raise SearchError("An error occurred with search")

    except SearchError as e:
        assert str(e) == "An error occurred with search "
