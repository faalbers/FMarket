import pandas as pd

class Account:
    def __init__(self, name, assets=None):
        self.name = name
        if isinstance(assets, type(None)):
            self.assets = pd.DataFrame(columns=['price_payed', 'quantity'])
            self.assets.index.name = 'symbol'
        else:
            self.assets = assets
