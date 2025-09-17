import pandas as pd
from dateutil.tz import tzlocal

class FTime:
    def __init__(self):
        pass

    @property
    def tz(self):
        return self.now_local.tzname()
    
    @property
    def now_local(self):
        return pd.Timestamp.now().tz_localize(tzlocal())
    
    @property
    def now_utc(self):
        return pd.Timestamp.now().tz_localize(tzlocal()).tz_convert('UTC')
    
    @property
    def date_local(self):
        return self.now_local.normalize()
    
    @property
    def date_utc(self):
        return self.now_utc.normalize()
    
    def get_quarter_begin(self, date):
        return (date - pd.offsets.QuarterEnd()).floor('D')
    
    def get_quarter_end(self, date):
        return (date + pd.offsets.QuarterEnd()).ceil('D')

    def get_offset(self, date, **arguments):
        return date + pd.offsets.DateOffset(**arguments)

    def get_from_ts_local(self, ts):
        return pd.to_datetime(ts, unit='s', utc=True).tz_convert('UTC').tz_convert(tzlocal())
    
    def get_from_ts_utc(self, ts):
        return pd.to_datetime(ts, unit='s', utc=True).tz_convert('UTC')
