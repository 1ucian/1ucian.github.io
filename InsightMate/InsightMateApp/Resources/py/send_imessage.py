import subprocess


def send_imessage(to: str, body: str):
    script = f'''tell application "Messages"
        send "{body}" to buddy "{to}" of (service 1 whose service type is iMessage)
    end tell'''
    subprocess.run(['osascript', '-e', script], check=True)


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 3:
        send_imessage(sys.argv[1], ' '.join(sys.argv[2:]))
