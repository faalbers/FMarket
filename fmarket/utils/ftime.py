import pandas as pd
from dateutil.tz import tzlocal
import calendar, holidays

class FTime:
    def __init__(self):
        pass

    @property
    def tz(self):
        return self.now_local.tzname()
    
    @property
    def now_naive(self):
        return pd.Timestamp.now()
    
    @property
    def now_local(self):
        return pd.Timestamp.now().tz_localize(tzlocal())
    
    @property
    def now_utc(self):
        return pd.Timestamp.now().tz_localize(tzlocal()).tz_convert('UTC')
    
    @property
    def now_ny(self):
        return pd.Timestamp.now().tz_localize(tzlocal()).tz_convert('US/Eastern')
    
    @property
    def date_local(self):
        return self.now_local.normalize()
    
    @property
    def date_utc(self):
        return self.now_utc.normalize()
    
    @property
    def date_ny(self):
        return self.now_ny.normalize()
    
    def get_quarter_begin(self, date):
        return self.get_offset(date - pd.offsets.QuarterEnd(), days=1).floor('D')
    
    def get_quarter_end(self, date):
        date = (date + pd.offsets.QuarterEnd()).ceil('D')
        date = self.get_offset(date, seconds=-1)
        return date
    
    def get_month_begin(self, date):
        return self.get_offset(date - pd.offsets.MonthEnd(), days=1).floor('D')
    
    def get_month_end(self, date):
        date = (date + pd.offsets.MonthEnd()).ceil('D')
        date = self.get_offset(date, seconds=-1)
        return date

    def get_year_begin(self, date):
        return self.get_offset(date - pd.offsets.YearEnd(), days=1).floor('D')

    def get_year_end(self, date):
        date = (date + pd.offsets.YearEnd()).ceil('D')
        date = self.get_offset(date, seconds=-1)
        return date

    def get_offset(self, date, **arguments):
        return date + pd.offsets.DateOffset(**arguments)

    def get_from_ts_local(self, ts):
        return pd.to_datetime(ts, unit='s', utc=True).tz_convert('UTC').tz_convert(tzlocal())
    
    def get_from_ts_utc(self, ts):
        return pd.to_datetime(ts, unit='s', utc=True).tz_convert('UTC')

    def get_date_naive(self, date=None, format=None, **arguments):
        if not isinstance(date, type(None)):
            if isinstance(format, type(None)):
                return pd.Timestamp(date)
            else:
                return pd.to_datetime(date, format=format)
        return pd.Timestamp(**arguments)

    def get_date_local(self, date=None, format=None, **arguments):
        if not isinstance(date, type(None)):
            if isinstance(format, type(None)):
                return pd.Timestamp(date).tz_localize(tzlocal())
            else:
                return pd.to_datetime(date, format=format).tz_localize(tzlocal())
        return pd.Timestamp(**arguments).tz_localize(tzlocal())
    
    def get_date_utc(self, date=None, format=None, **arguments):
        if not isinstance(date, type(None)):
            if isinstance(format, type(None)):
                return pd.Timestamp(date).tz_localize('UTC')
            else:
                return pd.to_datetime(date, format=format).tz_localize('UTC')
        return pd.Timestamp(**arguments).tz_localize('UTC')
    
    def get_date_ny(self, date=None, format=None, **arguments):
        if not isinstance(date, type(None)):
            if isinstance(format, type(None)):
                return pd.Timestamp(date).tz_localize('US/Eastern')
            else:
                return pd.to_datetime(date, format=format).tz_localize('US/Eastern')
        return pd.Timestamp(**arguments).tz_localize('US/Eastern')
    
    @property
    def is_market_open(self):
        now_ny = self.now_ny
        is_market_day = not (now_ny.date() in holidays.US()) and (calendar.weekday(self.now_ny.year, self.now_ny.month, self.now_ny.day) < 5)
        is_market_hours = now_ny.hour >= 9 and now_ny.hour < 17 # give it a bit of padding
        return (is_market_day and is_market_hours)
