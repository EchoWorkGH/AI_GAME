


from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model('img_4.png')  # 检测图片
results[0].plot()
# results = model(0)