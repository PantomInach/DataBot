import requests
import aiohttp

URL = "https://inspirobot.me/api?generate=true"


class Inspiro(object):
    """
    Class fetches the URL of quotes from inspirobot.me
    """

    @staticmethod
    def getPictureUrl():
        """
        Opens inspirobot site to fetch URL for a random new quote.
        Blocks thread. Use `getPictureUrlAsync` instead.
        """
        r = requests.get(URL)
        url = str(r.content)[2:-1]
        r.close()
        return url

    @staticmethod
    async def getPictureUrlAsync():
        """
        Opens inspirobot site to fetch URL for a random new quote.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                return await response.text()
