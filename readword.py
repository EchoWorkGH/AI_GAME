
import paddle
import paddleocr
from paddleocr import PaddleOCR

print("PaddlePaddle 版本:", paddle.__version__)
print("PaddleOCR 版本:", paddleocr.__version__)

img_path = r'D:\djj\gamecv\runs\detect\predict2\Screenshot_2026-01-28-14-37-51-09_97622d0c52f3ce6e6d31938c263a39ee.jpg'



# 初始化 OCR 引擎（默认自动下载中英文模型）
ocr = PaddleOCR(use_textline_orientation=True, lang='ch')  # 'ch' 表示中文，'en' 表示英文

result = ocr.ocr(img_path)

# 打印识别结果
for line in result:
    print(line)