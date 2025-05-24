# BlindQuants/Researchers/strategies.py

import backtrader as bt

# Removed the circular import:
# from .strategies import SmaCross, RsiStrategy, BollingerBandsStrategy, MacdStrategy, DonchianChannelsStrategy

# SMA Cross Strategy
class SmaCross(bt.Strategy):
    params = (
        ('pfast', 10),
        ('pslow', 30),
    )

    def __init__(self):
        self.sma1 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.pfast)
        self.sma2 = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.pslow)
        self.crossover = bt.indicators.CrossOver(self.sma1, self.sma2)
        self.order = None
        self.closed_trades = []

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
        else:
            if self.crossover < 0:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                trade = {
                    'type': 'Long',
                    'date_in': self.data.datetime.date(0).isoformat(),
                    'price_in': order.executed.price,
                    'size': order.executed.size,
                    'date_out': None,
                    'price_out': None,
                    'pnl_net': 0.0
                }
                self.closed_trades.append(trade)
            elif order.issell() and self.closed_trades:
                self.closed_trades[-1].update({
                    'date_out': self.data.datetime.date(0).isoformat(),
                    'price_out': order.executed.price,
                    'pnl_net': order.executed.pnl
                })
            self.order = None

# RSI Strategy
class RsiStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_upper', 70),
        ('rsi_lower', 30),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.order = None
        self.closed_trades = []

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsi < self.params.rsi_lower:
                self.order = self.buy()
        else:
            if self.rsi > self.params.rsi_upper:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                trade = {
                    'type': 'Long',
                    'date_in': self.data.datetime.date(0).isoformat(),
                    'price_in': order.executed.price,
                    'size': order.executed.size,
                    'date_out': None,
                    'price_out': None,
                    'pnl_net': 0.0
                }
                self.closed_trades.append(trade)
            elif order.issell() and self.closed_trades:
                self.closed_trades[-1].update({
                    'date_out': self.data.datetime.date(0).isoformat(),
                    'price_out': order.executed.price,
                    'pnl_net': order.executed.pnl
                })
            self.order = None

# Bollinger Bands Strategy
class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('bb_period', 20),
        ('bb_devfactor', 2.0),
    )

    def __init__(self):
        self.bbands = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor
        )
        self.order = None
        self.closed_trades = []

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.data.close < self.bbands.lines.bot:
                self.order = self.buy()
        else:
            if self.data.close > self.bbands.lines.top:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                trade = {
                    'type': 'Long',
                    'date_in': self.data.datetime.date(0).isoformat(),
                    'price_in': order.executed.price,
                    'size': order.executed.size,
                    'date_out': None,
                    'price_out': None,
                    'pnl_net': 0.0
                }
                self.closed_trades.append(trade)
            elif order.issell() and self.closed_trades:
                self.closed_trades[-1].update({
                    'date_out': self.data.datetime.date(0).isoformat(),
                    'price_out': order.executed.price,
                    'pnl_net': order.executed.pnl
                })
            self.order = None

# MACD Strategy
class MacdStrategy(bt.Strategy):
    params = (
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        self.order = None
        self.closed_trades = []

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.macd.macd > self.macd.signal:
                self.order = self.buy()
        else:
            if self.macd.macd < self.macd.signal:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                trade = {
                    'type': 'Long',
                    'date_in': self.data.datetime.date(0).isoformat(),
                    'price_in': order.executed.price,
                    'size': order.executed.size,
                    'date_out': None,
                    'price_out': None,
                    'pnl_net': 0.0
                }
                self.closed_trades.append(trade)
            elif order.issell() and self.closed_trades:
                self.closed_trades[-1].update({
                    'date_out': self.data.datetime.date(0).isoformat(),
                    'price_out': order.executed.price,
                    'pnl_net': order.executed.pnl
                })
            self.order = None

# Donchian Channels Strategy
class DonchianChannelsStrategy(bt.Strategy):
    params = (
        ('donchian_period', 20),
    )

    def __init__(self):
        self.donchian = bt.indicators.DonchianChannels(
            self.data.high,
            self.data.low,
            period=self.params.donchian_period
        )
        self.order = None
        self.closed_trades = []

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.data.close > self.donchian.lines.hi:
                self.order = self.buy()
        else:
            if self.data.close < self.donchian.lines.lo:
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                trade = {
                    'type': 'Long',
                    'date_in': self.data.datetime.date(0).isoformat(),
                    'price_in': order.executed.price,
                    'size': order.executed.size,
                    'date_out': None,
                    'price_out': None,
                    'pnl_net': 0.0
                }
                self.closed_trades.append(trade)
            elif order.issell() and self.closed_trades:
                self.closed_trades[-1].update({
                    'date_out': self.data.datetime.date(0).isoformat(),
                    'price_out': order.executed.price,
                    'pnl_net': order.executed.pnl
                })
            self.order = None