import os, sys, platform, subprocess

def remove_schedule():
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')

    if platform.system() == "Windows":
        task = "DailyStockEmail"
        result = subprocess.run(["schtasks", "/delete", "/tn", task, "/f"], capture_output=True)
        if result.returncode == 0:
            print(f"Done — task '{task}' removed.")
        else:
            print(f"Task '{task}' not found, nothing to remove.")
    else:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0 or script not in result.stdout:
            print("No matching cron job found.")
            return

        new_cron = "\n".join(
            line for line in result.stdout.splitlines()
            if script not in line
        ) + "\n"
        proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        proc.communicate(new_cron)
        print("Cron job removed.")

if __name__ == "__main__":
    remove_schedule()
