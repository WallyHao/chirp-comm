"""
接收端演示：从麦克风实时接收 chirp 消息，回调打印并可从列表拉取。
从项目根目录运行: python examples/recv_demo.py  或先 pip install -e . 再运行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time

from chirp_comm import ChirpReceiver


def on_received(msg):
    print(f"Real-time: {msg}")


receiver = ChirpReceiver(device=None, callback=on_received)
receiver.start()

try:
    while True:
        msgs = receiver.get_messages()
        if msgs:
            print(f"Pulled from list: {msgs}")
        time.sleep(1)
except KeyboardInterrupt:
    receiver.stop()
