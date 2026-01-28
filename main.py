# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import torch


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(torch.__version__)  # 查看 PyTorch 版本
    print(torch.cuda.is_available())  # 检查 GPU 是否可用

    # x = torch.randn(3, requires_grad=True)
    x = torch.tensor([1, 1, 1], dtype=torch.float, requires_grad=True)
    y = x * 2
    v = torch.tensor([10, 10, 1], dtype=torch.float)
    y.backward(v)
    print(x.grad)

    # # 创建需要梯度的张量
    # x = torch.tensor(2.0, requires_grad=True)
    #
    # # 定义计算图
    # y = x ** 2
    #
    # # 计算梯度
    # y.backward()
    #
    # # 查看梯度
    # print(x.grad)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x





net = Net()
