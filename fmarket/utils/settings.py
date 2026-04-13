import json
import pandas as pd

class Settings:
    def __init__(self):
        pass

    def get_ssel(self, ssel):
        with open('settings/ssel/%s.ssel' % ssel, 'r') as file:
            return self.get_ssel_file(file)
    
    def get_ssel_file(self, file):
        symbols = json.load(file)
        symbols = pd.DataFrame(symbols).T
        symbols.index.name = 'symbol'
        return symbols
    
    def set_ssel(self, ssel, data):
        with open('settings/ssel/%s.ssel' % ssel, 'w') as file:
            self.set_ssel_file(file, data)

    def set_ssel_file(self, file, data):
        data = data.T.to_dict()
        json.dump(data, file, indent=4)

    def get_filt(self, filt):
        with open('settings/filt/%s.filt' % filt, 'r') as file:
            return self.get_filt(file)
    
    def get_filt_file(self, file):
        filters = json.load(file)
        return filters
    
    def set_filt(self, filt, data):
        with open('settings/filt/%s.filt' % filt, 'w') as file:
            self.set_filt_file(file, data)

    def set_filt_file(self, file, data):
        json.dump(data, file, indent=4)

    def get_psel(self, psel):
        with open('settings/psel/%s.psel' % psel, 'r') as file:
            return self.get_psel_file(file)

    def get_psel_file(self, file):
        parmeters = json.load(file)
        return parmeters

    def set_psel(self, psel, data):
        with open('settings/psel/%s.psel' % psel, 'w') as file:
            self.set_psel_file(file, data)

    def set_psel_file(self, file, data):
        json.dump(data, file, indent=4)

