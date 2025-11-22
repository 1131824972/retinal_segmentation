import torch
import numpy as np
import cv2


dataset = np.load('pre/testdataset.npy', allow_pickle=True)


data = dataset[0][0]
label = dataset[0][1]

model = torch.load('model/bestmodel.pt').cpu()
# model = torch.load('训练好的模型权重/lastmosel.pt').cpu()

output = model(torch.Tensor(data.reshape(1,3,data.shape[-2],data.shape[-1]))).detach().numpy()

cv2.imshow('label',label[0])
cv2.imshow('output',output[0][0])
cv2.waitKey()
