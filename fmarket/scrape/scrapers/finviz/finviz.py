from ratelimit import limits, sleep_and_retry
from finvizfinance.quote import finvizfinance
import pandas as pd

class Finviz():
    def __init__(self):
        pass

    @sleep_and_retry
    @limits(calls=3, period=1)
    def get_news_limited(self, symbol):
        try:
            ticker = finvizfinance(symbol)
            news = ticker.ticker_news()
            if isinstance(news, type(None)):
                news = pd.DataFrame()
        except Exception as e:
            # self.logger.error("ticker news error: %s: %s" % (symbol, e))
            return pd.DataFrame()
        return news
    
    def request_news(self, symbol):
        return self.push_api_data(symbol, self.get_news_limited(symbol))

