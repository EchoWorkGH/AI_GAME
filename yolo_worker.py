import time
import random
import threading
import tkinter as tk
from PIL import Image
from mss import mss
from ultralytics import YOLO

# 导入 Windows API 相关库
import win32gui
import win32api
import win32con


class YOLOClickerWorker:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        self.is_running = False
        self.last_click_time = 0
        self.real_click_mode = True
        self.marker_window = None

        # 核心：存储绑定的窗口句柄
        self.hwnd = None

    def bind_window(self, hwnd):
        """由 AppUI 调用，绑定目标窗口句柄"""
        self.hwnd = hwnd

    def set_click_mode(self, real_click=True):
        self.real_click_mode = real_click

    def get_randomized_position(self, center_x, center_y, box_width, box_height):
        """获取目标框内的随机位置"""
        max_offset_x = min(box_width * 0.2, 15)
        max_offset_y = min(box_height * 0.2, 15)
        offset_x = random.uniform(-max_offset_x, max_offset_x)
        offset_y = random.uniform(-max_offset_y, max_offset_y)
        return center_x + offset_x, center_y + offset_y

    def perform_background_click(self, abs_x, abs_y, log_callback):
        """通过句柄发送后台点击事件"""
        if not self.hwnd:
            log_callback("错误：未绑定窗口句柄，请先锁定窗口")
            return

        try:
            # 1. 关键转换：屏幕绝对坐标 -> 窗口客户区相对坐标
            rel_x, rel_y = win32gui.ScreenToClient(self.hwnd, (int(abs_x), int(abs_y)))

            # 2. 构造消息参数 (LPARAM)
            lparam = win32api.MAKELONG(rel_x, rel_y)

            if self.real_click_mode:
                # 模拟双击：激活并触发
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                time.sleep(0.05)
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                time.sleep(0.05)
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                time.sleep(0.05)
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lparam)

                log_callback(f"后台点击成功 -> 句柄:{self.hwnd} | 相对坐标:({rel_x}, {rel_y})")
            else:
                self.show_click_instruction(abs_x, abs_y)
                log_callback(f"检测目标(演示) -> 窗口内位置:({rel_x}, {rel_y})")
        except Exception as e:
            log_callback(f"后台点击异常: {e}")

    def show_click_instruction(self, x, y):
        """在屏幕上显示红圈标记"""
        try:
            if self.marker_window:
                try:
                    self.marker_window.destroy()
                except:
                    pass
            self.marker_window = tk.Toplevel()
            self.marker_window.attributes("-alpha", 0.8, "-topmost", True, "-transparentcolor", "white")
            self.marker_window.overrideredirect(True)
            circle_size = 60
            self.marker_window.geometry(
                f"{circle_size}x{circle_size}+{int(x - circle_size // 2)}+{int(y - circle_size // 2)}")
            canvas = tk.Canvas(self.marker_window, bg="white", highlightthickness=0, width=circle_size,
                               height=circle_size)
            canvas.pack(fill="both", expand=True)
            canvas.create_oval(2, 2, circle_size - 2, circle_size - 2, outline="red", width=3)
            self.marker_window.after(1500, self._safe_destroy_marker)
        except:
            pass

    def _safe_destroy_marker(self):
        try:
            if self.marker_window:
                self.marker_window.destroy()
                self.marker_window = None
        except:
            pass

    def start_process(self, region, target_class, interval_ms, cooldown, log_callback, preview_callback):
        self.is_running = True
        L, T = int(region[0]), int(region[1])
        monitor = {"left": L, "top": T, "width": int(region[2]), "height": int(region[3])}

        log_callback(f"任务启动：句柄 [{self.hwnd}] | 目标 [{target_class}]")

        with mss() as sct:
            while self.is_running:
                loop_start = time.time()
                try:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    results = self.model.predict(img, conf=0.5, verbose=False)

                    current_time = time.time()
                    for box in results[0].boxes:
                        label = self.model.names[int(box.cls[0])]
                        if label == target_class:
                            if current_time - self.last_click_time > cooldown:
                                coords = box.xyxy[0].cpu().numpy()
                                abs_center_x = L + (coords[0] + coords[2]) / 2
                                abs_center_y = T + (coords[1] + coords[3]) / 2
                                box_w = coords[2] - coords[0]
                                box_h = coords[3] - coords[1]

                                target_abs_x, target_abs_y = self.get_randomized_position(
                                    abs_center_x, abs_center_y, box_w, box_h
                                )

                                # 执行后台点击
                                self.perform_background_click(target_abs_x, target_abs_y, log_callback)
                                self.last_click_time = current_time

                    res_plotted = results[0].plot()
                    preview_callback(Image.fromarray(res_plotted[..., ::-1]))

                except Exception as e:
                    log_callback(f"Worker异常: {e}")
                    break

                elapsed = (time.time() - loop_start) * 1000
                time.sleep(max(1, interval_ms - elapsed) / 1000.0)

    def stop(self):
        self.is_running = False