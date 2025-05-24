# Researchers/forms.py
from django import forms
from .models import Stock

TIMEFRAME_CHOICES = [
    ('1d', 'Daily (1d)'), ('1wk', 'Weekly (1wk)'), ('1mo', 'Monthly (1mo)'),
    ('1h', 'Hourly (1h)'), ('30m', '30 Minutes (30m)'), ('5m', '5 Minutes (5m)'),
]

STRATEGY_CHOICES = [
    ('sma_cross', 'Simple Moving Average Cross'),
    ('rsi_strategy', 'RSI (Oversold/Overbought)'),
    ('bb_strategy', 'Bollinger Bands (Mean Reversion)'),
    ('macd_strategy', 'MACD Crossover'),          # NEW
    ('donchian_strategy', 'Donchian Channel Breakout'), # NEW
]

class BacktestForm(forms.Form):
    stock = forms.ModelChoiceField(queryset=Stock.objects.all(), label="Select Stock")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Start Date")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="End Date")
    timeframe = forms.ChoiceField(choices=TIMEFRAME_CHOICES, initial='1d', label="Timeframe")
    initial_cash = forms.FloatField(initial=100000.0, label="Initial Cash")
    strategy = forms.ChoiceField(choices=STRATEGY_CHOICES, label="Select Strategy")

    # SMA Cross Parameters
    sma_fast_period = forms.IntegerField(initial=10, label="SMA Fast", required=False)
    sma_slow_period = forms.IntegerField(initial=30, label="SMA Slow", required=False)
    # RSI Strategy Parameters
    rsi_period = forms.IntegerField(initial=14, label="RSI Period", required=False)
    rsi_upper = forms.IntegerField(initial=70, label="RSI Overbought", required=False)
    rsi_lower = forms.IntegerField(initial=30, label="RSI Oversold", required=False)
    # Bollinger Bands Strategy Parameters
    bb_period = forms.IntegerField(initial=20, label="BB Period", required=False)
    bb_devfactor = forms.FloatField(initial=2.0, label="BB StDev Factor", required=False)
    # MACD Strategy Parameters
    macd_fast_period = forms.IntegerField(initial=12, label="MACD Fast EMA", required=False)
    macd_slow_period = forms.IntegerField(initial=26, label="MACD Slow EMA", required=False)
    macd_signal_period = forms.IntegerField(initial=9, label="MACD Signal EMA", required=False)
    # Donchian Channel Strategy Parameters
    donchian_period = forms.IntegerField(initial=20, label="Donchian Period", required=False)