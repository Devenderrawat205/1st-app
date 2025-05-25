# BlindQuants/Researchers/views.py

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Stock
from .forms import BacktestForm, STRATEGY_CHOICES, TIMEFRAME_CHOICES
from .strategies import SmaCross, RsiStrategy, BollingerBandsStrategy, MacdStrategy, DonchianChannelsStrategy
import yfinance as yf
import pandas as pd
import talib
import backtrader as bt
import openpyxl
from io import BytesIO
import quantstats as qs
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback
import json
from scipy.signal import find_peaks

# --- Main Stock Listing View ---
def stock_list(request):
    stocks = Stock.objects.all()
    message = "Displaying stocks from the database."
    if not stocks.exists():
        message = "No stocks found. Add some via the admin panel."
    context = {'stocks': stocks, 'message': message}
    return render(request, 'Researchers/stock_list.html', context)

# In BlindQuants/Researchers/views.py

def stock_analysis_view(request, stock_symbol):
    # Chart logic (reuse from stock_chart_view)
    chart_context = {}
    try:
        stock_obj = Stock.objects.get(symbol=stock_symbol.upper())
        # ... (copy chart logic here, set chart_context['plot_div'], etc.)
        # For brevity, use your existing chart logic and set chart_context
    except Exception as e:
        chart_context['error_message'] = f"Chart error: {str(e)}"
        stock_obj = None

    # Backtest logic (reuse from run_backtest_view)
    backtest_context = {}
    request.GET = request.GET.copy()
    request.GET['symbol'] = stock_symbol
    # Call your run_backtest_view logic here, but just get the context, not render

    # Merge contexts
    context = {**chart_context, **backtest_context, 'stock': stock_obj}
    return render(request, 'Researchers/stock_analysis.html', context)

# --- Stock Charting View (Enhanced with Plotly) ---
def stock_chart_view(request, stock_symbol):
    try:
        stock_obj = Stock.objects.get(symbol=stock_symbol.upper())
        selected_interval = request.GET.get('interval', '1d')
        show_sma_val = request.GET.get('sma', 'false')
        show_sma = show_sma_val.lower() == 'true'
        show_rsi_val = request.GET.get('rsi', 'false')
        show_rsi = show_rsi_val.lower() == 'true'
        show_bbands_val = request.GET.get('bbands', 'false')
        show_bbands = show_bbands_val.lower() == 'true'
        show_volume = True  # Always show volume for clarity

        # Validate parameters
        try:
            sma_period_chart = int(request.GET.get('sma_period', 20))
            rsi_period_chart = int(request.GET.get('rsi_period_c', 14))
            bbands_period_chart = int(request.GET.get('bbands_period_c', 20))
            bbands_dev_chart = float(request.GET.get('bbands_dev_c', 2.0))
        except (ValueError, TypeError) as e:
            return render(request, 'Researchers/stock_chart.html', {
                'error_message': f"Invalid parameter format: {str(e)}",
                'timeframe_choices': TIMEFRAME_CHOICES
            })

        valid_intervals = [choice[0] for choice in TIMEFRAME_CHOICES]
        if selected_interval not in valid_intervals:
            selected_interval = '1d'

        end_date = pd.Timestamp.now()
        if selected_interval in ['1wk', '1mo']:
            start_date = end_date - pd.DateOffset(years=10)
        elif selected_interval == '1h':
            start_date = end_date - pd.DateOffset(months=23)
        elif selected_interval in ['5m', '15m', '30m']:
            start_date = end_date - pd.DateOffset(days=59)
        else:
            start_date = end_date - pd.DateOffset(years=3)

        df = yf.download(stock_obj.symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'),
                         interval=selected_interval, progress=False)

        common_context_params = {
            'stock': stock_obj, 'timeframe_choices': TIMEFRAME_CHOICES, 'selected_interval': selected_interval,
            'show_sma': show_sma, 'sma_period_chart': sma_period_chart, 'show_rsi': show_rsi,
            'rsi_period_chart': rsi_period_chart, 'show_bbands': show_bbands, 'bbands_period_chart': bbands_period_chart,
            'bbands_dev_chart': bbands_dev_chart
        }

        if df.empty:
            return render(request, 'Researchers/stock_chart.html', {
                **common_context_params,
                'error_message': f"No data for {stock_obj.symbol} ({selected_interval})"
            })

        required_ohlc = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_ohlc):
            return render(request, 'Researchers/stock_chart.html', {
                **common_context_params,
                'error_message': f"Data for {stock_obj.symbol} incomplete (missing OHLC or Volume)."
            })

        # Create Plotly figure with subplots
        rows = 1 + show_volume + show_rsi
        heights = [0.6] + ([0.2] if show_volume else []) + ([0.2] if show_rsi else [])
        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                            row_heights=heights, subplot_titles=(stock_obj.symbol, "Volume" if show_volume else None, "RSI" if show_rsi else None))

        # Candlestick chart
        hover_texts = []
        for index, row_series in df.iterrows():
            text = (f"O: {float(row_series['Open']):.2f} H: {float(row_series['High']):.2f} "
                    f"L: {float(row_series['Low']):.2f} C: {float(row_series['Close']):.2f} "
                    f"V: {int(row_series['Volume'])}")
            hover_texts.append(text)

        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker_color=[('rgba(0,128,0,0.5)' if row_data['Close'] >= row_data['Open'] else 'rgba(255,0,0,0.5)')
                          for index, row_data in df.iterrows()],
            opacity=0.6
        ), row=2 if show_volume else 1, col=1)

        # SMA
        if show_sma and len(df) > sma_period_chart:
            df['SMA_Chart'] = talib.SMA(df['Close'], timeperiod=sma_period_chart)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['SMA_Chart'],
                name=f'SMA({sma_period_chart})',
                line=dict(color='orange', width=1.5),
                hoverinfo='x+y+text',
                text=[f"SMA: {val:.2f}" for val in df['SMA_Chart']]
            ), row=1, col=1)

        # Bollinger Bands
        if show_bbands and len(df) > bbands_period_chart:
            upper, middle, lower = talib.BBANDS(df['Close'], timeperiod=bbands_period_chart,
                                                nbdevup=bbands_dev_chart, nbdevdn=bbands_dev_chart)
            fig.add_trace(go.Scatter(x=df.index, y=upper, name='BB Upper', line=dict(color='rgba(180,180,180,0.5)', width=0.7)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=middle, name='BB Middle', line=dict(color='rgba(180,180,180,0.8)', width=1, dash='dot')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=lower, name='BB Lower', line=dict(color='rgba(180,180,180,0.5)', width=0.7)), row=1, col=1)

        # Volume subplot
        if show_volume:
            # ...
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=[('rgba(0,128,0,0.5)' if row_data['Close'] >= row_data['Open'] else 'rgba(255,0,0,0.5)')
                              for index, row_data in df.iterrows()],
                opacity=0.6  # slightly more opaque
            ), row=current_indicator_row, col=1)

        # RSI subplot
        if show_rsi and len(df) > rsi_period_chart:
            df['RSI_Chart'] = talib.RSI(df['Close'], timeperiod=rsi_period_chart)
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['RSI_Chart'],
                name=f'RSI({rsi_period_chart})',
                line=dict(color='blue', width=1.5)
            ), row=rows, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought", row=rows, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold", row=rows, col=1)

        # Support/Resistance Levels
        peaks, _ = find_peaks(df['High'], distance=20)
        troughs, _ = find_peaks(-df['Low'], distance=20)
        support = df['Low'].iloc[troughs].mean() if troughs.size > 0 else df['Low'].mean()
        resistance = df['High'].iloc[peaks].mean() if peaks.size > 0 else df['High'].mean()
        fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="Support", row=1, col=1)
        fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text="Resistance", row=1, col=1)

        # Candlestick Patterns (Doji example)
        doji = talib.CDLDOJI(df['Open'], df['High'], df['Low'], df['Close'])
        doji_dates = df.index[doji != 0]
        for date in doji_dates:
            fig.add_annotation(
                x=date,
                y=df['High'].loc[date],
                text="Doji",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-30,
                row=1,
                col=1
            )

        # Layout
        fig.update_layout(
            template='plotly_white',
            showlegend=True,
            height=800,
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis_rangeslider_visible=False,
            xaxis=dict(
                rangeselector=dict(
                    buttons=[
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all", label="All")
                    ]
                ),
                type="date",
                tickformat="%Y-%m-%d",
                showgrid=True,
                gridcolor='rgba(200,200,200,0.2)'
            ),
            yaxis=dict(
                title="Price ($)",
                tickformat=".2f",
                showgrid=True,
                gridcolor='rgba(200,200,200,0.2)'
            ),
            hovermode="x unified"
        )

        if show_volume:
            fig.update_yaxes(title_text="Volume", row=2 if show_rsi else 1 + show_volume, col=1)
        if show_rsi:
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=rows, col=1)

        plot_div = fig.to_json()

        context = {
            **common_context_params,
            'plot_div': plot_div,
            'error_message': None,
            'support_level': support,
            'resistance_level': resistance
        }
        return render(request, 'Researchers/stock_chart.html', context)
    except Stock.DoesNotExist:
        return render(request, 'Researchers/stock_chart.html', {
            'error_message': f"Stock {stock_symbol} not found.",
            'timeframe_choices': TIMEFRAME_CHOICES
        })
    except Exception as e:
        print(f"Error in stock_chart_view: {str(e)}")
        traceback.print_exc()
        return render(request, 'Researchers/stock_chart.html', {
            'error_message': f"Error charting: {str(e)}",
            'timeframe_choices': TIMEFRAME_CHOICES
        })

# --- Dynamic Indicator Update View ---
def update_indicator(request):
    if request.method == 'GET':
        symbol = request.GET.get('symbol')
        sma_period = request.GET.get('sma_period')
        rsi_period = request.GET.get('rsi_period')
        bbands_period = request.GET.get('bbands_period')
        bbands_dev = request.GET.get('bbands_dev')
        interval = request.GET.get('interval', '1d')

        try:
            stock_obj = Stock.objects.get(symbol=symbol.upper())
            end_date = pd.Timestamp.now()
            start_date = end_date - pd.DateOffset(years=3)
            df = yf.download(stock_obj.symbol, start=start_date.strftime('%Y-%m-%d'),
                             end=end_date.strftime('%Y-%m-%d'), interval=interval, progress=False)

            response_data = {}
            if sma_period:
                sma_period = int(sma_period)
                if len(df) > sma_period:
                    df['SMA'] = talib.SMA(df['Close'], timeperiod=sma_period)
                    response_data['sma_data'] = [{'x': row['Date'].isoformat(), 'y': float(row['SMA'])}
                                                 for row in df[['Date', 'SMA']].dropna().to_dict('records')]
            if rsi_period:
                rsi_period = int(rsi_period)
                if len(df) > rsi_period:
                    df['RSI'] = talib.RSI(df['Close'], timeperiod=rsi_period)
                    response_data['rsi_data'] = [{'x': row['Date'].isoformat(), 'y': float(row['RSI'])}
                                                 for row in df[['Date', 'RSI']].dropna().to_dict('records')]
            if bbands_period and bbands_dev:
                bbands_period = int(bbands_period)
                bbands_dev = float(bbands_dev)
                if len(df) > bbands_period:
                    upper, middle, lower = talib.BBANDS(df['Close'], timeperiod=bbands_period,
                                                        nbdevup=bbands_dev, nbdevdn=bbands_dev)
                    response_data['bbands_data'] = {
                        'upper': [{'x': row['Date'].isoformat(), 'y': float(row['upper'])}
                                  for row in df[['Date']].assign(upper=upper).dropna().to_dict('records')],
                        'middle': [{'x': row['Date'].isoformat(), 'y': float(row['middle'])}
                                   for row in df[['Date']].assign(middle=middle).dropna().to_dict('records')],
                        'lower': [{'x': row['Date'].isoformat(), 'y': float(row['lower'])}
                                  for row in df[['Date']].assign(lower=lower).dropna().to_dict('records')]
                    }
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# --- Save Drawing Annotations ---
def save_drawing(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            annotations = request.session.get('annotations', [])
            annotations.append({
                'type': 'line',
                'x0': data['start_date'],
                'y0': data['start_price'],
                'x1': data['end_date'],
                'y1': data['end_price'],
                'xref': 'x',
                'yref': 'y',
                'line': {'color': 'blue', 'width': 2}
            })
            request.session['annotations'] = annotations
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

# --- Unified Backtesting Form and Results View ---
def run_backtest_view(request):
    backtest_results_data = None
    error_message_display = None

    symbol = request.GET.get('symbol')
    if request.method == 'GET' and symbol:
        try:
            stock_obj = Stock.objects.get(symbol=symbol.upper())
            form = BacktestForm(initial={'stock': stock_obj})
        except Stock.DoesNotExist:
            form = BacktestForm()
    else:
        form = BacktestForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        stock_obj = form.cleaned_data['stock']
        start_date_dt = form.cleaned_data['start_date']
        end_date_dt = form.cleaned_data['end_date']
        selected_timeframe = form.cleaned_data['timeframe']
        initial_cash = form.cleaned_data['initial_cash']
        strategy_choice = form.cleaned_data['strategy']

        # Date range validation
        max_allowed_days = None
        limit_message_period = ""
        timeframe_name = dict(TIMEFRAME_CHOICES).get(selected_timeframe, selected_timeframe)
        if selected_timeframe in ['5m', '15m', '30m']:
            max_allowed_days = 59
            limit_message_period = "~60 days"
        elif selected_timeframe == '1h':
            max_allowed_days = 729
            limit_message_period = "~2 years"

        if max_allowed_days:
            requested_duration_days = (end_date_dt - start_date_dt).days
            if requested_duration_days < 0:
                error_message_display = "Start date cannot be after end date."
            elif requested_duration_days > max_allowed_days:
                suggested_start_date = end_date_dt - pd.Timedelta(days=max_allowed_days)
                error_message_display = (
                    f"Data for {timeframe_name} limited to {limit_message_period}. "
                    f"Your range ({requested_duration_days + 1} days) exceeds this. "
                    f"Try start date ~{suggested_start_date.strftime('%Y-%m-%d')}."
                )
            else:
                earliest_data_start = pd.Timestamp.now().normalize() - pd.Timedelta(days=max_allowed_days)
                if pd.Timestamp(start_date_dt) < earliest_data_start:
                    error_message_display = (
                        f"For {timeframe_name}, data older than {limit_message_period} from today "
                        f"(around {earliest_data_start.strftime('%Y-%m-%d')}) unavailable. Adjust start date."
                    )
        elif (end_date_dt - start_date_dt).days < 0:
            error_message_display = "Start date cannot be after end date."

        # Strategy parameters
        params = {}
        if not error_message_display:
            if strategy_choice == 'sma_cross':
                sma_fast = form.cleaned_data.get('sma_fast_period', 10)
                sma_slow = form.cleaned_data.get('sma_slow_period', 30)
                if sma_fast <= 0 or sma_slow <= 0:
                    error_message_display = "SMA periods must be positive."
                elif sma_fast >= sma_slow:
                    error_message_display = "SMA Fast period must be less than SMA Slow period."
                else:
                    params['sma_cross'] = {'pfast': sma_fast, 'pslow': sma_slow}
            elif strategy_choice == 'rsi_strategy':
                rsi_period = form.cleaned_data.get('rsi_period', 14)
                rsi_upper = form.cleaned_data.get('rsi_upper', 70)
                rsi_lower = form.cleaned_data.get('rsi_lower', 30)
                if rsi_period <= 0 or rsi_upper <= 0 or rsi_lower <= 0:
                    error_message_display = "RSI parameters must be positive."
                elif rsi_lower >= rsi_upper:
                    error_message_display = "RSI Lower must be less than RSI Upper."
                else:
                    params['rsi_strategy'] = {
                        'rsi_period': rsi_period,
                        'rsi_upper': rsi_upper,
                        'rsi_lower': rsi_lower
                    }
            elif strategy_choice == 'bb_strategy':
                bb_period = form.cleaned_data.get('bb_period', 20)
                bb_devfactor = form.cleaned_data.get('bb_devfactor', 2.0)
                if bb_period <= 0 or bb_devfactor <= 0:
                    error_message_display = "Bollinger Bands parameters must be positive."
                else:
                    params['bb_strategy'] = {
                        'bb_period': bb_period,
                        'bb_devfactor': bb_devfactor
                    }
            elif strategy_choice == 'macd_strategy':
                macd_fast = form.cleaned_data.get('macd_fast_period', 12)
                macd_slow = form.cleaned_data.get('macd_slow_period', 26)
                macd_signal = form.cleaned_data.get('macd_signal_period', 9)
                if macd_fast <= 0 or macd_slow <= 0 or macd_signal <= 0:
                    error_message_display = "MACD parameters must be positive."
                elif macd_fast >= macd_slow:
                    error_message_display = "MACD Fast period must be less than MACD Slow period."
                else:
                    params['macd_strategy'] = {
                        'macd_fast': macd_fast,
                        'macd_slow': macd_slow,
                        'macd_signal': macd_signal
                    }
            elif strategy_choice == 'donchian_strategy':
                donchian_period = form.cleaned_data.get('donchian_period', 20)
                if donchian_period <= 0:
                    error_message_display = "Donchian period must be positive."
                else:
                    params['donchian_strategy'] = {'donchian_period': donchian_period}
                    context = {
                        'form': form,
                        'results': backtest_results_data,
                        'error_message_from_view': error_message_display,
                        'symbol': symbol
                    }

        # If no validation errors, run backtest
        if not error_message_display:
            try:
                start_date_str = start_date_dt.strftime('%Y-%m-%d')
                end_date_str = end_date_dt.strftime('%Y-%m-%d')
                active_params = params[strategy_choice]
                df = yf.download(stock_obj.symbol, start=start_date_str, end=end_date_str,
                                 interval=selected_timeframe, progress=False)
                if df.empty:
                    error_message_display = f'No data found for {stock_obj.symbol} ({dict(TIMEFRAME_CHOICES).get(selected_timeframe)}).'
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    yfinance_map = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}
                    rename_map = {col: yfinance_map[col] for col in yfinance_map if col in df.columns}
                    df.rename(columns=rename_map, inplace=True)
                    bt_needed_cols = ['open', 'high', 'low', 'close', 'volume']
                    missing_cols = [col for col in bt_needed_cols if col not in df.columns]
                    if missing_cols:
                        error_message_display = f"Data for {stock_obj.symbol} missing columns: {', '.join(missing_cols)}."
                    else:
                        df_bt = df[bt_needed_cols].copy()
                        # Calculate minimum data needed based on the strategy
                        if strategy_choice == 'sma_cross':
                            min_data_needed = max(active_params['pfast'], active_params['pslow'])
                        elif strategy_choice == 'rsi_strategy':
                            min_data_needed = active_params['rsi_period']
                        elif strategy_choice == 'bb_strategy':
                            min_data_needed = active_params['bb_period']
                        elif strategy_choice == 'macd_strategy':
                            min_data_needed = active_params['macd_slow'] + active_params['macd_signal'] + 10
                        elif strategy_choice == 'donchian_strategy':
                            min_data_needed = active_params['donchian_period']
                        else:
                            min_data_needed = 30
                        if len(df_bt) < min_data_needed + 30:
                            error_message_display = (
                                f"Data length ({len(df_bt)}) for {stock_obj.symbol} insufficient "
                                f"(needs ~{min_data_needed + 30} bars for {dict(TIMEFRAME_CHOICES).get(selected_timeframe)})."
                            )
                        else:
                            df_bt['openinterest'] = 0
                            cerebro = bt.Cerebro()
                            cerebro.addobserver(bt.observers.Broker)
                            cerebro.broker.setcash(initial_cash)
                            data_feed = bt.feeds.PandasData(dataname=df_bt)
                            cerebro.adddata(data_feed)
                            cerebro.addsizer(bt.sizers.PercentSizer, percents=90)
                            strategy_map = {
                                'sma_cross': SmaCross,
                                'rsi_strategy': RsiStrategy,
                                'bb_strategy': BollingerBandsStrategy,
                                'macd_strategy': MacdStrategy,
                                'donchian_strategy': DonchianChannelsStrategy
                            }
                            cerebro.addstrategy(strategy_map[strategy_choice], **active_params)
                            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
                            cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
                            results = cerebro.run()
                            strat_instance = results[0]
                            final_value = cerebro.broker.getvalue()
                            trade_analysis = strat_instance.analyzers.trade_analyzer.get_analysis()
                            closed_trades = strat_instance.closed_trades if hasattr(strat_instance, 'closed_trades') else []
                            trade_stats = {
                                'total_trades': len(closed_trades),
                                'winning_trades': trade_analysis.get('won', {}).get('total', 0),
                                'losing_trades': trade_analysis.get('lost', {}).get('total', 0),
                                'max_profit_trade': trade_analysis.get('won', {}).get('pnl', {}).get('max', 0.0),
                                'max_loss_trade': abs(trade_analysis.get('lost', {}).get('pnl', {}).get('max', 0.0)),
                                'pnl_net': trade_analysis.get('pnl', {}).get('net', {}).get('total', 0.0)
                            }
                            processed_trades = []
                            current_balance = initial_cash
                            for idx, trade in enumerate(closed_trades):
                                pnl = trade.get('pnl_net', 0.0)
                                current_balance += pnl
                                processed_trades.append({
                                    **trade,
                                    'trade_number': idx + 1,
                                    'running_balance': current_balance
                                })
                            portfolio_stats = strat_instance.analyzers.pyfolio.get_analysis()
                            raw_returns = portfolio_stats.get('returns', {})
                            report_metrics = {}
                            returns_series = None
                            equity_plot_div = None
                            price_chart_with_signals_plot_div = None
                            if raw_returns:
                                try:
                                    rs = pd.Series(raw_returns)
                                    rs.index = pd.to_datetime(rs.index)
                                    if not rs.empty:
                                        returns_series = rs
                                        report_metrics = {
                                            'sharpe': qs.stats.sharpe(rs) if rs.std() != 0 else 'N/A',
                                            'sortino': qs.stats.sortino(rs) if rs.std() != 0 else 'N/A',
                                            'max_drawdown': qs.stats.max_drawdown(rs) * 100,
                                            'cagr': qs.stats.cagr(rs) * 100,
                                            'annual_volatility': qs.stats.volatility(rs, annualize=True) * 100
                                        }
                                except Exception as e_qs:
                                    report_metrics = {'error': 'Metrics calculation error'}
                            if returns_series is not None and not returns_series.empty:
                                eq_data = (1 + returns_series).cumprod() * initial_cash
                                fig_eq = go.Figure()
                                fig_eq.add_trace(go.Scatter(
                                    x=eq_data.index,
                                    y=eq_data,
                                    name='Portfolio Value',
                                    line=dict(color='blue')
                                ))
                                fig_eq.update_layout(
                                    template='plotly_white',
                                    title='Portfolio Value Over Time',
                                    yaxis_title='Portfolio Value ($)',
                                    height=400,
                                    margin=dict(l=50, r=50, t=50, b=50)
                                )
                                equity_plot_div = fig_eq.to_json()
                            if not df_bt.empty:
                                fig_price = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                                fig_price.add_trace(go.Candlestick(
                                    x=df_bt.index,
                                    open=df_bt['open'],
                                    high=df_bt['high'],
                                    low=df_bt['low'],
                                    close=df_bt['close'],
                                    name='Price',
                                    increasing_line_color='green',
                                    decreasing_line_color='red'
                                ), row=1, col=1)
                                fig_price.add_trace(go.Bar(
                                    x=df_bt.index,
                                    y=df_bt['volume'],
                                    name='Volume',
                                    marker_color=['green' if row['close'] >= row['open'] else 'red' for _, row in df_bt.iterrows()],
                                    opacity=0.5
                                ), row=2, col=1)
                                # Add trade signals
                                buy_sd, buy_sp, sell_sd, sell_sp = [], [], [], []
                                for trade in processed_trades:
                                    try:
                                        if trade.get('date_in') and trade.get('date_in') not in ["N/A", "Date Error"]:
                                            buy_sd.append(pd.to_datetime(trade['date_in']))
                                            buy_sp.append(trade['price_in'])
                                        if trade.get('date_out') and trade.get('date_out') not in ["N/A", "Date Error"]:
                                            sell_sd.append(pd.to_datetime(trade['date_out']))
                                            sell_sp.append(trade['price_out'])
                                    except (ValueError, TypeError):
                                        continue
                                if buy_sd:
                                    fig_price.add_trace(go.Scatter(
                                        x=buy_sd,
                                        y=buy_sp,
                                        mode='markers',
                                        name='Buy',
                                        marker=dict(color='green', size=10, symbol='triangle-up')
                                    ), row=1, col=1)
                                if sell_sd:
                                    fig_price.add_trace(go.Scatter(
                                        x=sell_sd,
                                        y=sell_sp,
                                        mode='markers',
                                        name='Sell',
                                        marker=dict(color='red', size=10, symbol='triangle-down')
                                    ), row=1, col=1)
                                fig_price.update_layout(
                                    template='plotly_white',
                                    title_text=f'{stock_obj.symbol} Price Chart & Signals ({dict(STRATEGY_CHOICES).get(strategy_choice)})',
                                    height=800,
                                    xaxis_rangeslider_visible=False,
                                    margin=dict(l=50, r=50, t=50, b=50),
                                    showlegend=True
                                )
                                fig_price.update_yaxes(title_text="Volume", row=2, col=1)
                                price_chart_with_signals_plot_div = fig_price.to_json()
                            download_params_str = (
                                f"?symbol={stock_obj.symbol}&start={start_date_str}&end={end_date_str}"
                                f"&strategy={strategy_choice}&cash={initial_cash}&timeframe={selected_timeframe}"
                            )
                            for p_name, p_val in active_params.items():
                                download_params_str += f"&{p_name}={p_val}"
                            backtest_results_data = {
                                'stock': stock_obj,
                                'initial_cash': initial_cash,
                                'final_value': final_value,
                                'strategy_name': dict(STRATEGY_CHOICES).get(strategy_choice),
                                'report_metrics': report_metrics,
                                'trade_stats': trade_stats,
                                'processed_trades_for_display': processed_trades,
                                'timeframe_used': dict(TIMEFRAME_CHOICES).get(selected_timeframe),
                                'download_params': download_params_str,
                                'equity_plot_div': equity_plot_div,
                                'price_chart_with_signals_plot_div': price_chart_with_signals_plot_div
                            }
            except Exception as e:
                error_message_display = f"Error during backtest: {str(e)}"
    elif request.method == 'POST':
        error_message_display = "Form data invalid. Please correct the errors."

    context = {
        'form': form,
        'results': backtest_results_data,
        'error_message_from_view': error_message_display,
        'symbol': symbol
    }
    print_final_context_for_debug(context)
    return render(request, 'Researchers/backtest_form.html', context)
# --- Helper function for debugging context ---
def print_final_context_for_debug(context):
    print("\n---- FINAL CONTEXT FOR TEMPLATE (run_backtest_view) ----")
    results_data = context.get('results')
    if results_data:
        print("  Backtest Results Data IS POPULATED:")
        print(f"    stock: {results_data.get('stock')}")
        print(f"    final_value: {results_data.get('final_value')}")
        print(f"    trade_stats total: {results_data.get('trade_stats', {}).get('total_trades')}")
        print(f"    equity_plot_div is None: {results_data.get('equity_plot_div') is None}")
        print(f"    price_chart_signals_plot_div is None: {results_data.get('price_chart_with_signals_plot_div') is None}")
    else:
        print("  Backtest Results Data (context['results']) IS NONE.")
    print(f"  Error message: {context.get('error_message_from_view')}")
    print(f"  Context keys: {list(context.keys())}")

# --- Download Backtest Report as Excel ---
def download_backtest_excel(request):
    required_params = ['symbol', 'start', 'end', 'strategy', 'timeframe', 'cash']
    missing_params = [p for p in required_params if not request.GET.get(p)]
    if missing_params:
        return HttpResponse(f"Error: Missing GET params for Excel: {missing_params}", status=400)

    symbol = request.GET.get('symbol')
    try:
        Stock.objects.get(symbol=symbol.upper())
    except Stock.DoesNotExist:
        return HttpResponse(f"Error: Stock {symbol} not found.", status=400)

    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    strategy_choice = request.GET.get('strategy')
    try:
        initial_cash = float(request.GET.get('cash'))
    except (ValueError, TypeError):
        return HttpResponse("Error: Invalid cash amount.", status=400)
    selected_timeframe = request.GET.get('timeframe')

    params = {}
    try:
        if strategy_choice == 'sma_cross':
            params = {'pfast': int(request.GET.get('pfast', 10)), 'pslow': int(request.GET.get('pslow', 30))}
        elif strategy_choice == 'rsi_strategy':
            params = {
                'rsi_period': int(request.GET.get('rsi_period', 14)),
                'rsi_upper': int(request.GET.get('rsi_upper', 70)),
                'rsi_lower': int(request.GET.get('rsi_lower', 30))
            }
        elif strategy_choice == 'bb_strategy':
            params = {
                'bb_period': int(request.GET.get('bb_period', 20)),
                'bb_devfactor': float(request.GET.get('bb_devfactor', 2.0))
            }
        elif strategy_choice == 'macd_strategy':
            params = {
                'macd_fast': int(request.GET.get('macd_fast_period', 12)),
                'macd_slow': int(request.GET.get('macd_slow_period', 26)),
                'macd_signal': int(request.GET.get('macd_signal_period', 9))
            }
        elif strategy_choice == 'donchian_strategy':
            params = {'donchian_period': int(request.GET.get('donchian_period', 20))}
    except (ValueError, TypeError) as e:
        return HttpResponse(f"Error: Invalid strategy parameters: {str(e)}", status=400)

    try:
        df = yf.download(symbol, start=start_str, end=end_str, interval=selected_timeframe, progress=False)
        if df.empty:
            return HttpResponse(f"Error: No data for {symbol}.", status=400)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        yfinance_map = {'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}
        rename_map = {col: yfinance_map[col] for col in yfinance_map if col in df.columns}
        df.rename(columns=rename_map, inplace=True)
        bt_needed_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in bt_needed_cols if col not in df.columns]
        if missing:
            return HttpResponse(f"Error: Data missing columns: {missing}.", status=400)

        df_excel = df[bt_needed_cols].copy()
        df_excel['openinterest'] = 0
        cerebro = bt.Cerebro(stdstats=False)
        cerebro.broker.setcash(initial_cash)
        symbol = stock_obj.symbol
        data_feed = bt.feeds.PandasData(dataname=df_excel)
        cerebro.adddata(data_feed)

        strategy_map = {
            'sma_cross': SmaCross,
            'rsi_strategy': RsiStrategy,
            'bb_strategy': BollingerBandsStrategy,
            'macd_strategy': MacdStrategy,
            'donchian_strategy': DonchianChannelsStrategy
        }
        cerebro.addstrategy(strategy_map[strategy_choice], **params)

        results = cerebro.run()
        strat_instance = results[0]
        trades = strat_instance.closed_trades if hasattr(strat_instance, 'closed_trades') else []
    except Exception as e:
        print(f"Excel Error: {str(e)}")
        traceback.print_exc()
        return HttpResponse(f"Error generating Excel: {str(e)}", status=500)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Trades"
    headers = ["#", "Type", "Date In", "Price In", "Date Out", "Price Out", "Size", "P/L (Net)"]
    ws.append(headers)
    trade_num = 1
    if trades:
        for trade in trades:
            ws.append([
                trade_num,
                trade.get('type'),
                trade.get('date_in'),
                f"{trade.get('price_in', 0):.2f}",
                trade.get('date_out'),
                f"{trade.get('price_out', 0):.2f}",
                trade.get('size'),
                f"{trade.get('pnl_net', 0):.2f}"
            ])
            trade_num += 1
    else:
        ws.append(["No trades made."])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Report_{symbol}_{strategy_choice}_{selected_timeframe}.xlsx'
    return response