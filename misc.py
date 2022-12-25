import requests
from datetime import date
from datetime import timedelta

bitcoin = "<:YOUR-EMOJI-NAME-HERE:YOUR-EMOJI-ID-HERE>"
    
    
win_slots = [
    """
🍑|🍎|🍑
🥥|🥥|🥥 ⬅️
🍑|🍎|🍐
    """,
    """
🥥|🍎|🍑
🍐|🍐|🍐 ⬅️
🍑|🍎|🥥
    """,
    """
🥥|🍐|🍑
🍎|🍎|🍎 ⬅️
🍑|🥥|🍐
    """,
    """
🥥|🍎|🍐
🍑|🍑|🍑 ⬅️
🥥|🍎|🍐
    """,
]
lost_slots = [
    """
🥥|🍎|🍑
🍑|🍐|🍑 ⬅️
🥥|🍎|🍐
    """,
    """
🥥|🍎|🍑
🍑|🥥|🥥 ⬅️
🥥|🍎|🍐
    """,
    """
🥥|🍐|🍑
🍑|🍎|🍎 ⬅️
🥥|🍎|🍐
    """,
    """
🥥|🍐|🍑
🍑|🍎|🍑 ⬅️
🥥|🍐|🥥
    """,
]


def get_price(company):
    API_KEY = "YOUR-API-KEY-HERE"
    today = date.today() - timedelta(days = 1)
    yesterday = today - timedelta(days = 2)
    request = f"https://api.polygon.io/v2/aggs/ticker/{company}/range/1/day/{yesterday}/{today}?adjusted=true&sort=asc&limit=120&apiKey={API_KEY}"
    response = requests.get(request).json()
    price = None
    if response["resultsCount"] >= 1:
        price = response["results"][0]["c"]
    return price
    
