import yaml
import os

# ================= 配置区域 =================
# 1. 指向你的 classes.txt 文件
classes_file = r'D:\djj\train_s\classes.txt'

# 2. 指向数据集根目录（包含 images/train 等的目录）
dataset_root = r'D:\djj\gamecv\datasets'

# 3. 输出的 yaml 文件名
output_yaml = 'wheat2.yaml'
# ===========================================

def generate_yolo_yaml():
    # 读取类别名称
    if not os.path.exists(classes_file):
        print(f"错误: 找不到文件 {classes_file}")
        return

    with open(classes_file, 'r', encoding='utf-8') as f:
        # 过滤掉空行并去除空格
        class_names = [line.strip() for line in f.readlines() if line.strip()]

    # 构建 YAML 数据结构
    data = {
        'path': dataset_root.replace('\\', '/'), # 统一使用正斜杠防止转义错误
        'train': 'images/train',
        'val': 'images/val',
        'test': '', # 如果没有测试集可以留空
        'nc': len(class_names),
        'names': {i: name for i, name in enumerate(class_names)}
    }

    # 写入文件
    with open(output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"✅ 成功生成: {output_yaml}")
    print(f"📊 类别总数 (nc): {data['nc']}")
    print(f"📝 类别列表: {list(data['names'].values())}")

if __name__ == "__main__":
    generate_yolo_yaml()