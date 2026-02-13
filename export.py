import os
import glob
from ultralytics import YOLO

# 假设你想遍历的文件夹路径是 'path_to_folder'
path_to_folder = r"D:\djj\train_s\save"

# 使用glob模块找到所有.pt文件
for pt_file in glob.glob(os.path.join(path_to_folder, "001yolo26s.pt")):
    model = YOLO(pt_file)
    # Export model
    success = model.export(format="onnx")