import talib as ta

class RSI:
    def __init__(self, chart):
        self.chart = chart
        self.rsi = ta.RSI(chart['Close'])
    
    def apply(self, lambda_func):
        return self.rsi.apply(lambda_func)

