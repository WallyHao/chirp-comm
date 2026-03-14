"""
发送端演示：在控制台输入 4 个字符，通过扬声器以 chirp 形式发送。
从项目根目录运行: python examples/send_demo.py  或先 pip install -e . 再运行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time

from chirp_comm import ChirpSender

sender = ChirpSender(device=None)

try:
    while True:
        text = input("Enter 4 chars to send: ")
        if len(text) != 4:
            print("Please enter exactly 4 characters.")
            continue
        sender.send(text)
except KeyboardInterrupt:
    sender.stop()
