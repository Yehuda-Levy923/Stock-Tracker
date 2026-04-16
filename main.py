import os, sys
import fetch_and_plot
from send_email import send_email
from setup_schedule import setup_schedule

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_schedule()
    else:
        rsi_signals = fetch_and_plot.fetch_and_plot()
        send_email(rsi_signals)
        for f in fetch_and_plot.CHART_FILES:
            if os.path.exists(f):
                os.remove(f)