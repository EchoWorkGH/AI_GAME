import os


def fix_yolo_labels(folder_path):
    # 支持的后缀名
    if not os.path.exists(folder_path):
        print(f"错误: 找不到文件夹 {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    count = 0

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        modified = False

        for line in lines:
            parts = line.split()
            if len(parts) > 0 and parts[0] == '10':
                parts[0] = '0'
                new_lines.append(" ".join(parts) + "\n")
                modified = True
            else:
                new_lines.append(line)

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            count += 1
            print(f"已修正: {file_name}")

    print(f"\n处理完成！共修改了 {count} 个文件。")


# --- 使用方法 ---
# 将下面的路径替换为你真实的 labels 文件夹路径
my_labels_path = r'D:\djj\gamecv\data\labels\train'
fix_yolo_labels(my_labels_path)