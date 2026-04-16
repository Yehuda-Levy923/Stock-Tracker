import os
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for headless servers
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

TICKERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tickers.txt')


def load_tickers():
    with open(TICKERS_FILE) as f:
        return [line.strip().upper() for line in f if line.strip() and not line.startswith('#')]


TICKERS = load_tickers()
CHART_FILES = [f'{t}_chart.png' for t in TICKERS]


def local_highs_avg(series, order=5):
    rolled_max = series.rolling(2 * order + 1, center=True).max()
    peaks = series[series == rolled_max]
    return peaks.mean() if not peaks.empty else series.max()


def local_lows_avg(series, order=5):
    rolled_min = series.rolling(2 * order + 1, center=True).min()
    troughs = series[series == rolled_min]
    return troughs.mean() if not troughs.empty else series.min()


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd(series, fast=12, slow=26, signal_span=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_span, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger(series, window=20, num_std=2):
    sma = series.rolling(window).mean()
    std = series.rolling(window).std()
    return sma + num_std * std, sma, sma - num_std * std


def fetch_and_plot():
    end = datetime.now()
    start_1y = end - timedelta(days=365)

    all_data = yf.download(TICKERS, start=start_1y, end=end)
    prices_all = all_data['Close']
    volume_all = all_data['Volume']

    rsi_latest = {}
    for ticker in TICKERS:
        prices_1y = prices_all[ticker].dropna()
        volume_1y = volume_all[ticker].dropna()

        prices = prices_1y.iloc[-90:]
        volume = volume_1y.iloc[-90:].fillna(0)

        ceiling = local_highs_avg(prices_1y)
        floor = local_lows_avg(prices_1y)

        # compute on the full year so the first bars aren't thrown off by a short window
        rsi = compute_rsi(prices_1y).iloc[-90:]
        last_rsi = rsi.iloc[-1] if not rsi.dropna().empty else float('nan')
        rsi_latest[ticker] = last_rsi

        macd_line, signal_line, histogram = [s.iloc[-90:] for s in compute_macd(prices_1y)]
        bb_upper, bb_mid, bb_lower = [s.iloc[-90:] for s in compute_bollinger(prices_1y)]
        ma20 = prices_1y.rolling(20).mean().iloc[-90:]
        ma50 = prices_1y.rolling(50).mean().iloc[-90:]

        if last_rsi < 30:
            signal_label, title_color = 'BUY SIGNAL', 'green'
        elif last_rsi > 70:
            signal_label, title_color = 'SELL SIGNAL', 'red'
        else:
            signal_label, title_color = '', 'black'

        fig = plt.figure(figsize=(14, 14))
        gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1.5, 1.5], hspace=0.08)
        ax1 = fig.add_subplot(gs[0])
        ax_vol = fig.add_subplot(gs[1], sharex=ax1)
        ax_rsi = fig.add_subplot(gs[2], sharex=ax1)
        ax_macd = fig.add_subplot(gs[3], sharex=ax1)

        ax1.plot(prices.index, prices, color='steelblue', linewidth=1.5, label='Close')
        ax1.plot(ma20.index, ma20, color='orange', linewidth=1.2, linestyle='--', label='20-day MA')
        ax1.plot(ma50.index, ma50, color='red', linewidth=1.2, linestyle='--', label='50-day MA')
        ax1.fill_between(prices.index, bb_lower, bb_upper, alpha=0.08, color='gray')
        ax1.plot(bb_upper.index, bb_upper, color='gray', linewidth=0.8, linestyle=':', label='Bollinger Bands')
        ax1.plot(bb_lower.index, bb_lower, color='gray', linewidth=0.8, linestyle=':')
        ax1.axhline(ceiling, color='orangered', linestyle=':', linewidth=1.5, label=f'1y Resistance: ${ceiling:.2f}')
        ax1.axhline(floor, color='dodgerblue', linestyle=':', linewidth=1.5, label=f'1y Support: ${floor:.2f}')
        title = f'{ticker} — Past 90 Trading Days'
        if signal_label:
            title += f'  [{signal_label}]'
        ax1.set_title(title, color=title_color, fontweight='bold', fontsize=13)
        ax1.set_ylabel('Closing Price (USD)')
        ax1.legend(loc='upper left', fontsize=7.5, ncol=2)
        ax1.grid(True, linestyle='--', alpha=0.5)
        plt.setp(ax1.get_xticklabels(), visible=False)

        vol_colors = ['green' if c >= 0 else 'red' for c in prices.diff().fillna(0)]
        ax_vol.bar(volume.index, volume, color=vol_colors, alpha=0.6, width=0.8)
        ax_vol.set_ylabel('Volume', fontsize=8)
        ax_vol.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
        ax_vol.grid(True, linestyle='--', alpha=0.3)
        plt.setp(ax_vol.get_xticklabels(), visible=False)

        ax_rsi.plot(rsi.index, rsi, color='purple', linewidth=1.5)
        ax_rsi.axhline(70, color='red', linestyle='--', linewidth=1, label='Overbought (70)')
        ax_rsi.axhline(30, color='green', linestyle='--', linewidth=1, label='Oversold (30)')
        ax_rsi.fill_between(rsi.index, 70, 100, alpha=0.07, color='red')
        ax_rsi.fill_between(rsi.index, 0, 30, alpha=0.07, color='green')
        ax_rsi.set_ylabel('RSI (14)', fontsize=8)
        ax_rsi.set_ylim(0, 100)
        ax_rsi.yaxis.set_major_locator(mticker.MultipleLocator(20))
        ax_rsi.legend(loc='upper left', fontsize=7.5)
        ax_rsi.grid(True, linestyle='--', alpha=0.5)
        plt.setp(ax_rsi.get_xticklabels(), visible=False)

        hist_colors = ['green' if v >= 0 else 'red' for v in histogram.fillna(0)]
        ax_macd.plot(macd_line.index, macd_line, color='blue', linewidth=1.2, label='MACD')
        ax_macd.plot(signal_line.index, signal_line, color='orange', linewidth=1.2, label='Signal (9)')
        ax_macd.bar(histogram.index, histogram, color=hist_colors, alpha=0.5, width=0.8, label='Histogram')
        ax_macd.axhline(0, color='black', linewidth=0.8)
        ax_macd.set_ylabel('MACD', fontsize=8)
        ax_macd.set_xlabel('Date')
        ax_macd.legend(loc='upper left', fontsize=7.5)
        ax_macd.grid(True, linestyle='--', alpha=0.5)

        fig.autofmt_xdate()
        fig.savefig(f'{ticker}_chart.png', dpi=120, bbox_inches='tight')
        plt.close(fig)

    return rsi_latest
