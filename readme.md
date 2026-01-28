

### 安裝 PyTorch
pip install torch torchvision torchaudio
目前沒有GPU 所以支持GPU的先不用




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


D:/djj/gamecv/data/
├── images/
│   ├── train/   # 训练用图片
│   └── val/     # 验证用图片（这里放你要问的文件）
└── labels/
    ├── train/   # 训练用标注
    └── val/     # 验证用标注（这里放对应的 .txt）



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



字段,当前值,含义解读
Epoch 7/100,7/100,当前是第 7 轮训练（总共 100 轮）。
GPU_mem,0G,显存占用。显示 0G 通常是因为模型太小（n系列）或数据量极小。
box_loss,2.694,框定位损失。数值越小，模型预测的框位置越准。
cls_loss,8.203,类别分类损失。这个值很高，说明模型目前对“这是什么物体”还很糊涂。
Instances,4,这一批次中出现的物体数量。说明训练集是有标签的。
Class: all,3,验证集里一共有 3 张图片。
Instances,0,重点：验证集里识别到的物体数量为 0。 这证实了上面的警告——YOLO 没读到 val 的标签。
P / R / mAP,0,准确率、召回率、平均精度全为 0。因为没有标签做对比，所以无法计算。

