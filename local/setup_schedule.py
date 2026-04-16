import os, sys, platform, subprocess

def setup_schedule():
    # main.py lives one directory up from this script
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'main.py')
    python = sys.executable

    if platform.system() == "Windows":
        task = "DailyStockEmail"
        cmd = [
            "schtasks", "/create", "/tn", task,
            "/tr", f'"{python}" "{script}"',
            "/sc", "daily", "/st", "15:12", "/f"
        ]
        subprocess.run(cmd, check=True)
        print(f"Done — task '{task}' created. Check Task Scheduler to verify.")
    else:
        job = f"0 9 * * * {python} '{script}'"
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing = result.stdout if result.returncode == 0 else ""

        if script in existing:
            print("Already in crontab, nothing to do.")
            return

        new_cron = existing.rstrip('\n') + f"\n{job}\n"
        proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        proc.communicate(new_cron)
        print("Cron job added. Run 'crontab -l' to check.")

if __name__ == "__main__":
    setup_schedule()
