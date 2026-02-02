

##pip install mss pillow

import os
import time
from mss import mss
from PIL import Image

import os
import time
import tkinter as tk
from mss import mss
from PIL import Image


class AreaSelector:
    """拖拽选区工具"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-alpha', 0.3)  # 设置透明度
        self.root.attributes('-fullscreen', True)  # 全屏
        self.root.attributes("-topmost", True)  # 置顶
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None
        self.selection = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=2)

    def on_move_press(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(self.start_x - end_x)
        height = abs(self.start_y - end_y)

        if width > 5 and height > 5:
            self.selection = (left, top, width, height)
            self.root.destroy()

    def get_selection(self):
        self.root.mainloop()
        return self.selection


def start_capture(output_folder, interval_ms=500):
    # 1. 唤起选区界面
    print("请在屏幕上拖拽选择截图区域（按 Esc 退出）...")
    selector = AreaSelector()
    region = selector.get_selection()

    if not region:
        print("未选择有效区域，程序退出。")
        return

    # 2. 准备截图
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    monitor = {
        "left": region[0],
        "top": region[1],
        "width": region[2],
        "height": region[3]
    }

    print(f"开始截图！区域: {region}, 频率: {interval_ms}ms/张")
    print("保存位置: " + os.path.abspath(output_folder))
    print("按 Ctrl+C 停止截图")

    try:
        with mss() as sct:
            count = 0
            while True:
                start_time = time.time()

                # 抓取图像
                sct_img = sct.grab(monitor)
                file_path = os.path.join(output_folder, f"cap_{int(time.time() * 1000)}.png")

                # 转换并保存 (使用 Image.frombytes 转换 BGRX 为 RGB)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.save(file_path)

                count += 1
                if count % 10 == 0:
                    print(f"已捕获 {count} 张...")

                # 精准控制间隔
                elapsed = (time.time() - start_time) * 1000
                time.sleep(max(0, interval_ms - elapsed) / 1000.0)
    except KeyboardInterrupt:
        print("\n捕获任务已手动停止。")


if __name__ == "__main__":
    # 配置
    SAVE_DIR = "my_captures"
    MS_INTERVAL = 500

    start_capture(SAVE_DIR, MS_INTERVAL)