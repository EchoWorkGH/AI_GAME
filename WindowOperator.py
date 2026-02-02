import win32gui
import win32con
import win32api
import time

class WindowOperator:
    def __init__(self, window_title):
        self.title = window_title
        self.hwnd = self._get_hwnd()

    def _get_hwnd(self):
        """寻找目标窗口句柄"""
        hwnd = win32gui.FindWindow(None, self.title)
        if not hwnd:
            print(f"找不到窗口: {self.title}")
        return hwnd

    def wake_up(self):
        """唤醒并置顶窗口（不移动鼠标）"""
        if self.hwnd:
            # 如果窗口是最小化的，恢复它
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            # 强制带到前台
            win32gui.SetForegroundWindow(self.hwnd)

    def background_click(self, rel_x, rel_y):
        """
        后台发送点击消息，不影响物理鼠标
        rel_x, rel_y: 目标在截图区域内的坐标，
        如果识别区域不是从(0,0)开始，需在此处计算好偏移。
        """
        if self.hwnd:
            # 这里的坐标必须是相对于目标窗口客户区(Client Area)的
            arg = win32api.MAKELONG(int(rel_x), int(rel_y))
            # 发送按下消息
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, arg)
            time.sleep(0.01) # 模拟按下的间隔
            # 发送抬起消息
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, arg)