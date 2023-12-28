import webbrowser as web
PLAYER_URL: str = "https://console.videodb.io/player"


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
