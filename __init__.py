"""Main file for simple back tester."""
from dataclasses import dataclass

import quantstats as qs
import pandas as pd
from tqdm import tqdm

qs.extend_pandas()

class Backtest:
    def __init__(self, data, start_date, end_date, strategy, benchmark_ticker=None):
        self._data = data
        self._start_date = start_date
        self._end_date = end_date
        self._strategy = strategy
        self._benchmark_ticker = benchmark_ticker
        self._daily_returns = pd.Series(name="Close", dtype="float64")

        self.holdings = {}

    def _update_returns(self, current_date):
        returns = 0

        for ticker, amount in self.holdings.items():
            loc = self._data[ticker].index.get_loc(current_date)
            current_price = self._data[ticker].iloc[loc]["close"]
            past_price = self._data[ticker].iloc[loc - 1]["close"]
            change = (current_price - past_price) / past_price

            returns += amount * change

        self._daily_returns.loc[current_date] = returns


    def sell(self, ticker, percent):
        if percent == 1:
            del self.holdings[ticker]
            return

        self.holdings[ticker] -= self.holdings[ticker] * (1 - percent)

    def sell_all(self):
        self.holdings = {}

    def buy(self, ticker, percent=1):
        del self.holdings[ticker]
        new_holdings = {ticker: percent}
        other_holdings_sum = sum(self.holdings.values())

        for ticker, amount in self.holdings.items():
            new_holdings[ticker] = amount / other_holdings_sum


    def run(self):
        start_index = self._start_date
        data_to_pass = {ticker:data.loc[:start_index, "close"].to_list() for ticker, data in self._data.items()}

        for date in tqdm(pd.date_range(self._start_date, self._end_date)):
            if date in self._data[self._benchmark_ticker].index:
                self._update_returns(date)

                for ticker, data in self._data.items():
                    data_to_pass[ticker].append(data.loc[date, "close"])

                self._strategy(self, data_to_pass)

    def report(self):
        qs.reports.html(self._daily_returns, output=True)

