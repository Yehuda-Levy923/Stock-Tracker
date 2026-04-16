import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from fetch_and_plot import CHART_FILES

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
EMAIL_TO = os.environ.get('EMAIL_TO', EMAIL_ADDRESS)


def send_email(rsi_signals):
    buy = {t: v for t, v in rsi_signals.items() if v < 30}
    sell = {t: v for t, v in rsi_signals.items() if v > 70}

    def rsi_color(v):
        if v < 30:
            return '#1a7a1a'
        if v > 70:
            return '#cc0000'
        return '#333333'

    def signal_label(v):
        if v < 30:
            return 'Oversold / Buy'
        if v > 70:
            return 'Overbought / Sell'
        return 'Neutral'

    all_rows = ''.join(
        f'<tr style="border-bottom:1px solid #eee">'
        f'<td style="padding:6px 14px;font-weight:bold">{t}</td>'
        f'<td style="padding:6px 14px;color:{rsi_color(v)};font-weight:bold;text-align:right">{v:.1f}</td>'
        f'<td style="padding:6px 14px;color:{rsi_color(v)}">{signal_label(v)}</td>'
        f'</tr>'
        for t, v in sorted(rsi_signals.items())
    )
    summary_table = f'''
    <h3 style="margin-bottom:6px">RSI Summary of All Tracked Stocks</h3>
    <table style="border-collapse:collapse;font-size:14px;min-width:320px">
      <thead>
        <tr style="background:#f5f5f5">
          <th style="padding:7px 14px;text-align:left;border-bottom:2px solid #ddd">Ticker</th>
          <th style="padding:7px 14px;text-align:right;border-bottom:2px solid #ddd">RSI (14)</th>
          <th style="padding:7px 14px;text-align:left;border-bottom:2px solid #ddd">Signal</th>
        </tr>
      </thead>
      <tbody>{all_rows}</tbody>
    </table>'''

    def signal_rows(signals, color):
        return ''.join(
            f'<tr>'
            f'<td style="color:{color};font-weight:bold;padding:4px 12px">{t}</td>'
            f'<td style="color:{color};padding:4px 12px">RSI: {v:.1f}</td>'
            f'</tr>'
            for t, v in sorted(signals.items())
        )

    alert_section = ''
    if buy or sell:
        buy_block = ''
        if buy:
            buy_block = f'''
            <div style="background:#f0fff0;border-left:4px solid green;padding:10px 16px;margin:10px 0">
              <h3 style="color:green;margin:0 0 6px">Buy Signals: RSI below 30 (Oversold)</h3>
              <table>{signal_rows(buy, "green")}</table>
            </div>'''
        sell_block = ''
        if sell:
            sell_block = f'''
            <div style="background:#fff0f0;border-left:4px solid #cc0000;padding:10px 16px;margin:10px 0">
              <h3 style="color:#cc0000;margin:0 0 6px">Sell Signals: RSI above 70 (Overbought)</h3>
              <table>{signal_rows(sell, "#cc0000")}</table>
            </div>'''
        alert_section = f'<h3 style="color:#555;margin-top:20px">Actionable Signals Today</h3>{buy_block}{sell_block}'

    no_signal_note = (
        '' if (buy or sell)
        else '<p style="color:#555">No stocks are currently in overbought or oversold territory.</p>'
    )

    html = f'''
    <html><body style="font-family:sans-serif;max-width:700px;margin:auto;color:#222;padding:16px">
    <h2 style="border-bottom:2px solid #ddd;padding-bottom:8px">
      Daily Stock Update {datetime.now():%Y-%m-%d}
    </h2>
    {no_signal_note}
    {alert_section}
    {summary_table}
    <p style="color:#999;font-size:12px;margin-top:20px">
      Charts for all tracked stocks (past 90 days) are attached.
    </p>
    </body></html>
    '''

    msg = EmailMessage()
    msg['Subject'] = f'Daily Stock Update: {datetime.now():%Y-%m-%d}'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_TO
    msg.set_content('See the HTML version of this email for the signal summary.')
    msg.add_alternative(html, subtype='html')

    for chart_file in CHART_FILES:
        with open(chart_file, 'rb') as f:
            msg.add_attachment(f.read(), maintype='image', subtype='png', filename=chart_file)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent.")
