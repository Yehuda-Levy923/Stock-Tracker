import os
import fetch_and_plot
from send_email import send_email

if __name__ == "__main__":
    rsi_signals = fetch_and_plot.fetch_and_plot()
    send_email(rsi_signals)
    for f in fetch_and_plot.CHART_FILES:
        if os.path.exists(f):
            os.remove(f)
