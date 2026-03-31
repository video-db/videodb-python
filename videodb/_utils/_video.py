import webbrowser as web

PLAYER_URL: str = "https://console.videodb.io/player"


def player_url_to_embed_url(player_url: str) -> str:
    """Convert a /watch player URL to an /embed URL.

    :param str player_url: The player URL (e.g., https://player.videodb.io/watch?v=slug)
    :return: The embed URL (e.g., https://player.videodb.io/embed?v=slug)
    :rtype: str
    :raises ValueError: If the URL format is invalid or missing the 'v' parameter
    """
    if not player_url:
        raise ValueError("player_url is required to generate embed URL")

    if "/watch?" not in player_url:
        raise ValueError("player_url must contain '/watch?' path")

    if "v=" not in player_url.split("/watch?", 1)[1]:
        raise ValueError("player_url must contain a 'v' query parameter")

    return player_url.replace("/watch?", "/embed?", 1)


def build_iframe_embed_code(
    player_url: str,
    width: str = "100%",
    height: int = 405,
    title: str = "VideoDB Player",
    allow_fullscreen: bool = True,
) -> str:
    """Build an iframe embed HTML string from a player URL.

    :param str player_url: The player URL to embed
    :param str width: Width of the iframe (default: "100%")
    :param int height: Height of the iframe in pixels (default: 405)
    :param str title: Title attribute for the iframe (default: "VideoDB Player")
    :param bool allow_fullscreen: Whether to allow fullscreen (default: True)
    :return: HTML iframe string
    :rtype: str
    :raises ValueError: If player_url is empty or height is not positive
    """
    if not player_url:
        raise ValueError("player_url is required to generate embed code")

    if height <= 0:
        raise ValueError("height must be a positive integer")

    embed_url = player_url_to_embed_url(player_url)
    fullscreen_attr = " allowfullscreen" if allow_fullscreen else ""

    return (
        f'<iframe src="{embed_url}" '
        f'width="{width}" height="{height}" '
        f'title="{title}" frameborder="0"{fullscreen_attr}></iframe>'
    )


def play_stream(url: str):
    """Play a stream url in the browser/ notebook

    :param str url: The url of the stream
    :return: The player url if the stream is opened in the browser or the iframe if the stream is opened in the notebook
    """
    player = f"{PLAYER_URL}?url={url}"
    opend = web.open(player)
    if not opend:
        try:
            from IPython.display import IFrame

            player_width = 800
            player_height = 400
            return IFrame(player, player_width, player_height)
        except ImportError:
            return player
    return player
