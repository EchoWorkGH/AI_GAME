import time
import pyautogui
from mss import mss
from PIL import Image
from ultralytics import YOLO


class YOLOClickerWorker:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        self.is_running = False
        self.last_click_time = 0

    def start_process(self, region, target_class, interval_ms, cooldown, log_callback, preview_callback):
        """
        核心运行循环
        region: (L, T, W, H)
        log_callback: 用于向 UI 发送日志的函数
        preview_callback: 用于向 UI 发送识别图的函数
        """
        self.is_running = True
        L, T = int(region[0]), int(region[1])
        monitor = {"left": L, "top": T, "width": int(region[2]), "height": int(region[3])}

        with mss() as sct:
            while self.is_running:
                start_time = time.time()
                try:
                    # 1. 抓图
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                    # 2. 推理
                    results = self.model.predict(img, conf=0.5, verbose=False)

                    # 3. 逻辑处理
                    for box in results[0].boxes:
                        label = self.model.names[int(box.cls[0])]
                        if label == target_class:
                            coords = box.xyxy[0].cpu().numpy()
                            # 坐标转换：相对 -> 绝对
                            screen_x = L + (coords[0] + coords[2]) / 2
                            screen_y = T + (coords[1] + coords[3]) / 2

                            # 点击动作
                            if time.time() - self.last_click_time > cooldown:
                                pyautogui.click(screen_x, screen_y)
                                self.last_click_time = time.time()
                                log_callback(f"点击 {target_class}: ({int(screen_x)}, {int(screen_y)})")

                    # 4. 预览回调
                    res_plotted = results[0].plot()
                    preview_callback(Image.fromarray(res_plotted[..., ::-1]))

                except Exception as e:
                    log_callback(f"后台异常: {e}")
                    break

                # 动态频率控制
                elapsed = (time.time() - start_time) * 1000
                time.sleep(max(1, interval_ms - elapsed) / 1000.0)

    def stop(self):
        self.is_running = False