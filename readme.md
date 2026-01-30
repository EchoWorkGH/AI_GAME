

### 安裝 PyTorch
pip install torch torchvision torchaudio
目前沒有GPU 所以支持GPU的先不用

標註用 labelimg 但是經常崩潰  
現在換x-anylabeling  
pip install x-anylabeling -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install importlib-metadata -i https://pypi.tuna.tsinghua.edu.cn/simple

https://github.com/CVHub520/X-AnyLabeling/blob/main/docs/en/get_started.md

# CPU [Windows/Linux/macOS]
pip install x-anylabeling-cvhub[cpu]

# CUDA 12.x is the default GPU option [Windows/Linux]
pip install x-anylabeling-cvhub[gpu]

# CUDA 11.x [Windows/Linux]
pip install x-anylabeling-cvhub[gpu-cu11]

xanylabeling

## 后续直接只用yolo来搞

[doc](https://developer.aliyun.com/article/1430595)
Annotations文件夹：用来存放使用labelimg给每张图片标注后的xml文件，后面会讲解如何使用labelimg进行标注。
Images文件夹：用来存放原始的需要训练的数据集图片，图片格式为jpg格式。
ImageSets文件夹：用来存放将数据集划分后的用于训练、验证、测试的文件。
Labels文件夹：用来存放将xml格式的标注文件转换后的txt格式的标注文件。


predefined_classes.txt 要放这个位置。。。
C:\Users\36117\.conda\envs\labelimg\Lib\site-packages\labelImg\data\predefined_classes.txt

D:\djj\gamecv\data\Images

D:\djj\gamecv\data\Annotations

```
D:/djj/gamecv/data/
├── images/
│   ├── train/   # 训练用图片
│   └── val/     # 验证用图片（这里放你要问的文件）
└── labels/
    ├── train/   # 训练用标注
    └── val/     # 验证用标注（这里放对应的 .txt）
```

# data.yaml
path: D:/djj/gamecv/data  # 数据集根目录

# 训练集指向多个文件夹
train: 
  - images/train_old    # 文件夹 1
  - images/train_new    # 文件夹 2
  - images/web_data     # 文件夹 3

# 验证集也可以指向多个
val:
  - images/val_standard
  - images/val_challenge

names:
  0: enemy
  1: friend



| 模型名称 | 字母含义 | 文件大小 | 速度 (CPU/移动端) | 精度 (mAP) | 适用场景 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **yolov8n.pt** | **Nano** | **约 6MB** | **极快** | 基础 | 手机、嵌入式设备、追求高帧率的游戏 |
| **yolov8s.pt** | Small | 约 22MB | 快 | 中等 | 兼顾速度与精度的实时检测 |
| **yolov8m.pt** | Medium | 约 50MB | 一般 | 高 | 算力充足的桌面端应用 |
| **yolov8l.pt** | Large | 约 80MB | 较慢 | 极高 | 复杂场景、对速度要求不高的环境 |
| **yolov8x.pt** | Extra Large | 约 130MB | 慢 | 巅峰 | 竞赛、高精度离线分析 |

训练时的log含义

| 字段 | 含义 | 状态解读 |
| :--- | :--- | :--- |
| **Epoch** | 当前轮次 / 总轮次 | `2/30` 表示总共计划练 30 轮，现在是第 2 轮。 |
| **GPU_mem** | 显存占用 | `0G` 说明模型极小（yolov8n）或显存占用未达 1GB。 |
| **box_loss** | 矩形框定位损失 | 数值越低，表示模型画的框位置越准。 |
| **cls_loss** | 类别分类损失 | 数值越低，表示模型认错物体的概率越小。 |
| **dfl_loss** | 分布聚焦损失 | 用于精细微调框的边界，数值越低，框的边缘越贴合目标。 |
| **Instances** | 当前批次的目标数 | 这一组训练图片中总共包含 10 个被标注的物体。 |
| **Size** | 输入图片尺寸 | `640` 表示图片被缩放到 640x640 像素进入网络。 |

训练成果

| 字段名称 | 含义 | 说明                                                    |
| :--- | :--- |:------------------------------------------------------|
| **Class** | 类别 | `all` 表示所有类别的平均值，或者显示具体的类别名称。                         |
| **Images** | 图片总数 | 验证集中用于测试的图片数量。                                        |
| **Instances** | 标注总数 | 验证集中所有物体标签的总个数。                                       |
| **Box(P)** | 精确率 (Precision) | 模型找出的物体中，真正正确的比例（查准率）。                                |
| **R** | 召回率 (Recall) | 所有真实物体中，被模型成功找出的比例（查全率）。                              |
| **mAP50** | 平均精度 (IoU=0.5) | 在交并比阈值为 0.5 时的平均精度，是衡量模型性能的核心指标。                      |
| **mAP50-95** | 综合平均精度 | 在不同 IoU 阈值（0.5 到 0.95）下的平均精度，数值越高代表模型越稳健。 0.6-0.7就是很好 |


训练输出

| 文件名 | 含义 | 解读建议 |
| :--- | :--- | :--- |
| **results.csv** | 训练数据详表 | 包含每轮的 Loss、mAP、P、R 等原始数据。 |
| **results.png** | 综合趋势图 | 将 `results.csv` 可视化，看曲线是否平滑下降或上升。 |
| **F1_curve.png** | F1 分数曲线 | Precision 和 Recall 的平衡点，数值越高越好。 |
| **P_curve.png** | 精确率曲线 | 随置信度变化的查准率。 |
| **R_curve.png** | 召回率曲线 | 随置信度变化的查全率。 |
| **PR_curve.png** | PR 曲线 | 曲线下方包围面积越大，说明模型综合性能越强。 |
| **confusion_matrix.png** | **混淆矩阵** | 看模型最容易把 A 错认成 B，还是认成背景。 |



