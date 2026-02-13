import os

# 1. 设置路径
# label_path = r'D:\djj\train_s\002HPtest\val\labels' # 你的标签文件夹
label_path = r'D:\djj\train_s\002HPtest\train\labels' # 你的标签文件夹
nc_limit = 25 # 你的 yaml 中 nc 的值

def check_labels(path, limit):
    errors = []
    for file in os.listdir(path):
        print(f"file {file} ")
        if file.endswith('.txt'):
            file_path = os.path.join(path, file)
            with open(file_path, 'r') as f:
                lines = f.readlines()
                for line_num, line in enumerate(lines):
                    cls_id = int(line.split()[0])
                    # 检查类别 ID 是否越界
                    if cls_id >= limit:
                        errors.append(f"文件: {file} | 行: {line_num+1} | 错误 ID: {cls_id}")
                    # 检查坐标是否在 0-1 之间（归一化检查）
                    coords = list(map(float, line.split()[1:]))
                    if any(c < 0 or c > 1 for c in coords):
                        errors.append(f"文件: {file} | 行: {line_num+1} | 坐标越界: {coords}")
    return errors

results = check_labels(label_path, nc_limit)
if results:
    print(f"共发现 {len(results)} 处错误：")
    for r in results: print(r)
else:
    print("未发现明显的类别或坐标越界错误。")