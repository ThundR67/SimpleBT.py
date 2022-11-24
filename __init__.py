"""Main file for simple back tester."""
from dataclasses import dataclass

import quantstats as qs
import pandas as pd
from tqdm import tqdm

class Backtest:
    """Class to backtest a daily trading strategy."""
    def __init__(self, data, start_date, end_date, strategy, benchmark_ticker=None):
        """
        @data: dict with keys as ticker symbols and values as pandas dataframes with columns "open", "high", "low", "close", "volume"
        @start_date: start date of backtest
        @end_date: end date of backtest
        @strategy: function that takes in a Backtest object and a dict of data and runs the strategy
        @benchmark_ticker: ticker symbol of benchmark to compare to. Ticker must be in @data
        """
        self._data = data
        self._start_date = start_date
        self._end_date = end_date
        self._strategy = strategy
        self._benchmark_ticker = benchmark_ticker
        self._daily_returns = pd.Series(name="Close", dtype="float64")

        self.holdings = {}

    def _update_returns(self, current_date):
        """
        Update @self._daily_returns based on current holdings
        from previous date to @current_date.
        """
        self._daily_returns.loc[current_date] = 0

        for ticker, amount in self.holdings.items():
            loc = self._data[ticker].index.get_loc(current_date)
            current_price = self._data[ticker].iloc[loc]["close"]
            past_price = self._data[ticker].iloc[loc - 1]["close"]
            change = (current_price - past_price) / past_price

            self._daily_returns.loc[current_date] += amount * change


    def sell(self, ticker, percent):
        """Sell @percent of @ticker from current holdings."""
        if percent == 1:
            del self.holdings[ticker]
            return

        self.holdings[ticker] -= self.holdings[ticker] * (1 - percent)

    def sell_all(self):
        """Sell all holdings."""
        self.holdings = {}

    def buy(self, ticker, percent=1):
        """Buy @percent of @ticker and rebalances other holdings."""
        if percent == 1:
            self.holdings = {ticker: 1}
            return

        holdings_sum = sum(self.holdings.values())

        if (1 - holdings_sum) >= percent:
            self.holdings[ticker] = percent
            return

        other_holdings_sum = holdings_sum
        if ticker in self.holdings:
            other_holdings_sum -= self.holdings[ticker]
            del self.holdings[ticker]

        for other_ticker, amount in self.holdings.items():
            self.holdings[other_ticker] = (amount / other_holdings_sum) * (1 - percent)

        self.holdings[ticker] = percent


    def run(self):
        """Runs backtest."""
        start_index = self._start_date
        data_to_pass = {ticker:data.loc[:start_index, "close"].to_list() for ticker, data in self._data.items()}

        for date in tqdm(pd.date_range(self._start_date, self._end_date)):
            if date in self._data[self._benchmark_ticker].index:
                self._update_returns(date)

                for ticker, data in self._data.items():
                    data_to_pass[ticker].append(data.loc[date, "close"])

                self._strategy(self, data_to_pass)

    def report(self):
        """Generates a HTML report of backtest."""
        qs.reports.html(self._daily_returns, output=True)
