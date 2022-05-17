import requests


class Inspiro(object):
    """
    Class fetches the URL of quotes from inspirobot.me
    """

    @staticmethod
    def getPictureUrl():
        """
        Opens inspirobot site to fetch URL for a random new quote.
        """
        r = requests.get("https://inspirobot.me/api?generate=true")
        return str(r.content)[2:-1]
