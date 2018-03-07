from .FinancialSymbol import FinancialSymbol
from .Enums import Currency, Period
import pandas as pd
import numpy as np
from .Settings import change_column_name
from contracts import contract
from typing import List
import datetime as dtm
import dateutil.relativedelta


class PortfolioAsset:

    def __init__(self, symbol: FinancialSymbol,
                 start_period: pd.Period, end_period: pd.Period, currency: Currency):
        self.symbol = symbol
        self.start_period = start_period
        self.end_period = end_period

        datetime_now = dtm.datetime.now()
        if (datetime_now + dtm.timedelta(days=1)).month == datetime_now.month:
            datetime_now -= dateutil.relativedelta.relativedelta(months=1)
        period_end = pd.Period(datetime_now, freq='M')  # can't use Period.now because `now` is mocked in tests
        self.values = self.__transform_values_according_to_period(start_period=start_period, end_period=period_end)
        self.values = self.values[(self.values['period'] >= start_period) &
                                  (self.values['period'] <= end_period)]
        self.period_min = self.values['period'].min()
        self.period_max = self.values['period'].max()
        self.currency = currency
        self.__convert_currency(currency_to=currency)
        self.values[change_column_name] = self.values['close'].pct_change().fillna(value=0.)

    def __transform_values_according_to_period(self, start_period, end_period):
        vals = self.symbol.values(start_period, end_period)

        if self.symbol.period == Period.DAY:
            vals['period'] = vals['date'].dt.to_period('M')
            if vals['date'].max() < dtm.datetime.now() - dateutil.relativedelta.relativedelta(months=1):
                vals = vals[vals['period'] < vals['period'].max()]
            vals_not_current_period = vals['period'] != pd.Period.now(freq='M')
            vals_lastdate_indices = vals.groupby(['period'])['date'].transform(max) == vals['date']
            vals = vals[vals_not_current_period & vals_lastdate_indices]
            del vals['date']
        elif self.symbol.period == Period.MONTH:
            vals['period'] = vals['date'].dt.to_period('M')
            del vals['date']
        elif self.symbol.period == Period.DECADE:
            vals = vals[vals['period'].str[-1] == '3']
            vals['period'] = vals['period'].apply(lambda p: pd.Period(p[:-2], freq='M'))
        else:
            raise Exception('Unexpected type of `period`')

        vals.sort_values(by='period', ascending=True, inplace=True)
        vals.index = vals['period']
        return vals

    def __convert_currency(self, currency_to: Currency):
        from .FinancialSymbolsSourceContainer import FinancialSymbolsSourceContainer as Fssc

        currency_from = self.symbol.currency
        if currency_from == currency_to:
            return

        currency_rate = Fssc.currency_symbols_registry().convert(currency_from, currency_to)
        self.values = self.values.merge(currency_rate, on='period', how='left', suffixes=('', '_currency_rate'))
        self.values['close'] = self.values['close'] * self.values['close_currency_rate']
        self.values.index = self.values['period']
        self.values.sort_values(by='period', ascending=True, inplace=True)
        del self.values['close_currency_rate']

    def close(self):
        return self.values['close'].values

    def rate_of_return(self):
        return self.values[change_column_name].values

    def period(self):
        return self.values['period'].values

    def accumulated_rate_of_return(self):
        return (self.rate_of_return() + 1.).cumprod() - 1.

    def risk(self, period='year'):
        """
        Returns risk of the asset

        :param period:
            month - returns monthly risk

            year - returns risk approximated to yearly value
        """
        return Portfolio(assets=[self], weights=np.array([1.0]),
                         start_period=self.start_period, end_period=self.end_period,
                         currency=self.currency).risk(period=period)

    @contract(
        years_ago='int,>0|None|list[int,>0]',
    )
    def compound_annual_growth_rate(self, years_ago=None):
        months_in_year = 12
        if years_ago is None:
            years_total = (self.period_max - self.period_min) / months_in_year
            close_changes = self.values[change_column_name].values
            cagr = (close_changes + 1.).prod() ** (1 / years_total) - 1.
            return cagr
        elif isinstance(years_ago, list):
            return np.array([self.compound_annual_growth_rate(years_ago=y) for y in years_ago])
        else:
            months_count = years_ago * months_in_year
            if self.period_min > self.period_max - months_count:
                return self.compound_annual_growth_rate(years_ago=None)
            period_start = self.period_max - months_count
            close_changes = self.values[self.values['period'] > period_start][change_column_name].values
            cagr = (close_changes + 1.).prod() ** (1 / years_ago) - 1.
            return cagr


class Portfolio:
    def __init__(self,
                 assets: List[PortfolioAsset],
                 weights: np.array,
                 start_period: pd.Period, end_period: pd.Period,
                 currency: Currency):
        self.weights = weights.reshape(-1, 1)
        self.period_min = max(start_period, *[a.period_min for a in assets])
        self.period_max = min(end_period, *[a.period_max for a in assets])

        self.assets = [PortfolioAsset(a.symbol,
                                      start_period=self.period_min,
                                      end_period=self.period_max,
                                      currency=currency) for a in assets]

    def assets_weighted(self):
        return list(zip(self.assets, self.weights.T[0]))

    def accumulated_rate_of_return(self):
        return (self.rate_of_return() + 1.).cumprod() - 1.

    def risk(self, period='year'):
        """
        Returns risk of the asset

        :param period:
            month - returns monthly risk

            year - returns risk approximated to yearly value
        """
        if period == 'month':
            return np.std(self.rate_of_return()[1:])
        elif period == 'year':
            mean = np.mean(1 + self.rate_of_return()[1:])
            return np.sqrt((self.risk('month') ** 2 + mean ** 2) ** 12 - mean ** 24)
        else:
            raise Exception('unexpected value of `period` {}'.format(period))

    @contract(
        years_ago='int,>0|None|list[int,>0]',
    )
    def compound_annual_growth_rate(self, years_ago=None):
        cagrs_per_asset = np.vstack([a.compound_annual_growth_rate(years_ago=years_ago)
                                     for a in self.assets])
        cagrs = cagrs_per_asset.sum(axis=0)
        if cagrs.shape == (1,):
            cagrs = cagrs[0]
        return cagrs

    def rate_of_return(self):
        assets_rate_of_returns = np.vstack(a.rate_of_return() for a in self.assets)
        return (assets_rate_of_returns * self.weights).sum(axis=0)