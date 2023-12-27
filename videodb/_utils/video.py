import webbrowser as web


def play_url(url: str) -> bool:
    opend = web.open(url)
    if not opend:
        try:
            from IPython.display import IFrame

            player_width = 800
            player_height = 400
            IFrame(url, player_width, player_height)
        except ImportError:
            return False
    return True
