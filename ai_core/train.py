import numpy as np
import torch
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, Dataset
from Unet import UNet
import copy
from tqdm import tqdm  # 导入进度条库

traindata = np.load("pre/trainingdataset.npy", allow_pickle=True)
testdata = np.load("pre/testdataset.npy", allow_pickle=True)


# 数据库加载
class Dataset(Dataset):
    def __init__(self, data):
        self.len = len(data)
        self.x_data = torch.from_numpy(np.array(list(map(lambda x: x[0], data)), dtype=np.float32))
        self.y_data = torch.from_numpy(np.array(list(map(lambda x: x[1], data)))).float()

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.len


# 数据库dataloader
Train_dataset = Dataset(traindata)
Test_dataset = Dataset(testdata)
dataloader = DataLoader(Train_dataset, batch_size=1, shuffle=True)
testloader = DataLoader(Test_dataset, batch_size=1, shuffle=False)

# 训练设备选择GPU还是CPU
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# 模型初始化
model = UNet(3, 1)
model.to(device)

# 损失函数选择
criterion = torch.nn.BCEWithLogitsLoss()
criterion.to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

train_loss = []
test_loss = []


# 训练函数
def train(epoch):
    model.train()
    mloss = []

    # 添加训练进度条
    pbar = tqdm(dataloader, desc=f'Epoch {epoch} Training', leave=False)

    for data in pbar:
        datavalue, datalabel = data
        datavalue, datalabel = datavalue.to(device), datalabel.to(device)

        datalabel_pred = model(datavalue)
        loss = criterion(datalabel_pred, datalabel)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        mloss.append(loss.item())

        # 更新进度条显示当前损失
        pbar.set_postfix({'Loss': f'{loss.item():.4f}'})

    epoch_train_loss = torch.mean(torch.Tensor(mloss)).item()
    train_loss.append(epoch_train_loss)
    return epoch_train_loss


# 测试函数
def test():
    model.eval()
    mloss = []

    # 添加测试进度条
    pbar = tqdm(testloader, desc='Testing', leave=False)

    with torch.no_grad():
        for testdata in pbar:
            testdatavalue, testdatalabel = testdata
            testdatavalue, testdatalabel = testdatavalue.to(device), testdatalabel.to(device)

            testdatalabel_pred = model(testdatavalue)
            loss = criterion(testdatalabel_pred, testdatalabel)
            mloss.append(loss.item())

            # 更新进度条显示当前损失
            pbar.set_postfix({'Loss': f'{loss.item():.4f}'})

        epoch_test_loss = torch.mean(torch.Tensor(mloss)).item()
        test_loss.append(epoch_test_loss)
        return epoch_test_loss


bestmodel = None
bestepoch = None
bestloss = np.inf

# 添加总体训练进度条
epochs = 100
pbar_epochs = tqdm(range(1, epochs + 1), desc='Total Training Progress')

for epoch in pbar_epochs:
    train_loss_value = train(epoch)
    test_loss_value = test()

    # 更新总体进度条信息
    pbar_epochs.set_postfix({
        'Train Loss': f'{train_loss_value:.4f}',
        'Test Loss': f'{test_loss_value:.4f}',
        'Best Loss': f'{bestloss:.4f}'
    })

    print(f"\nEpoch {epoch}: Train Loss: {train_loss_value:.4f}, Test Loss: {test_loss_value:.4f}")

    if test_loss_value < bestloss:
        bestloss = test_loss_value
        bestepoch = epoch
        bestmodel = copy.deepcopy(model)
        print(f"New best model at epoch {epoch} with loss {bestloss:.4f}")

print(f"\n最佳轮次为: {bestepoch}, 最佳损失为: {bestloss:.4f}")

torch.save(model, "model/lastmodel.pt")
torch.save(bestmodel, "model/bestmodel.pt")

# 绘制损失曲线
plt.figure(figsize=(10, 6))
plt.plot(train_loss, label='Train Loss')
plt.plot(test_loss, label='Test Loss')
plt.legend()
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training and Test Loss')
plt.grid(True)
plt.savefig('training_loss.png')
plt.show()