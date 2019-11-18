import os
import sys
import numpy as np
from scipy.misc import imread, imresize
import cv2
from scipy.misc import imshow
# from scipy.misc import imwrite
import torch
from PIL import Image
import torch
import matplotlib.pyplot as plt

# import warnings
# warnings.filterwarnings('error')

def read_img(path, gray=True, reshape=False, shape=(256,256)):
    if gray:
        img = imread(path)[:,:,1]
        if reshape:
            img = cv2.resize(img,shape,interpolation=cv2.INTER_NEAREST)

    else:
        img = imread(path)
        if reshape:
            img = cv2.resize(img,shape,interpolation=cv2.INTER_NEAREST)

    return img

def delF(img):
    Fx, Fy = np.gradient(img)
    return np.sqrt(Fx**2 + Fy**2)

def maxEigofHess(img):
    Fx, Fy = np.gradient(img)
    Fxx, Fxy = np.gradient(Fx)
    _, Fyy = np.gradient(Fy)

    eig = (Fxx + Fyy + ((Fxx - Fyy)**2 + (2*Fxy)**2)**0.5)/2.0
    return eig

def getForegroundMask(img):
    img = np.array(img)
    img[img>50] = 255
    img[img<=50] = 0
    return img


def extractFeature(img,mean,std):
    img = np.array(img,dtype=np.uint8)
    fg = getForegroundMask(img)
    # img = normalizeImage(img,mean,std)
    img[fg!=0] = 255-img[fg!=0]
    img = clahe(img)
    img = adjustGamma(img)
    img[fg==0]=0
    # img = cv2.GaussianBlur(img,(41,41),1)
    # img = 255.0-img
    img = img/255
    print(np.max(img))
    featImg = np.zeros((img.shape[0]*img.shape[1], 3))
    featImg[:, 0] = (img.reshape(-1))
    featImg[:, 1] = delF(img).reshape(-1)
    featImg[:, 2] = maxEigofHess(img).reshape(-1)
    # featImg[:, 1] = 1.0
    # featImg[:, 2] = 1.0
    # featImg[:,2] = 1

    return featImg


def get_dataset(img_path, label_path):
    images = []
    for img in os.listdir(img_path):
        images.append(read_img(img_path + '/' + img))
    labels = []
    for label in os.listdir(label_path):
        labels.append(read_img(label_path + '/' + label))

    return np.array(images), np.array(labels)

def adjustGamma(img,gamma=1.0):
    invGamma = 1.0/gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(np.array(img, dtype = np.uint8), table)

def clahe(img,clipLimit=4.0,tileGridSize=(10,10)):
    clahe = cv2.createCLAHE(clipLimit=clipLimit,tileGridSize=tileGridSize)
    return clahe.apply(np.array(img,dtype=np.uint8))


def getNormalizationStatistics(img_path):
    images = []
    for img in os.listdir(img_path):
        images.append(read_img(os.path.join(img_path,img),gray=True))
    images = np.array(images)
    return np.mean(images),np.std(images)

def normalizeImage(img,mean,std):
    img = (img - mean)/std
    img = (img - np.min(img))/(np.max(img)-np.min(img))*255.0
    return img

def run_model(model, img, label):
    img = cv2.imread(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)[:, :, 1].reshape(605, 700)
    img = extractFeature(img, 85.1, 48.9).reshape(605*700, 3)
    pred = model(torch.from_numpy(img).float()).detach().numpy()
    argmax_pred = np.argmax(pred, 1)
    # print(argmax_pred)
    thresh_pred = 1*(pred[:, 1] > 0.8)
    label = cv2.imread(label, cv2.IMREAD_GRAYSCALE).reshape(605, 700)
    label = label//255
    label = label.reshape(605*700)
    # print((argmax_pred == label).sum())
    eq = thresh_pred == label
    true_pos = (eq*label).sum()
    # print(np.max((1-eq)*(1-label)))
    false_neg = ((1-eq)*(1-label)).sum()
    false_pos = eq.sum() - true_pos
    print(true_pos, false_neg, true_pos/(true_pos + false_neg))
    print((label == np.zeros(605*700)).sum())
    pred = pred[:, 1]
    pred = pred*255
    imshow(argmax_pred.reshape(605, 700))



if __name__ == "__main__":
    # img = read_img('../data/images/im0001.ppm', gray=True)

    mean,std = getNormalizationStatistics('../data/images')
    print(mean, std)
    img = read_img('../data/images/im0001.ppm',gray=True)
    fg = getForegroundMask(img)
    img = np.array(img,dtype=np.uint8)
    img[fg!=0] = 255-img[fg!=0]
    # img = normalizeImage(img,mean,std)
    img = clahe(img)
    img = adjustGamma(img)
    img[fg==0]=0
    # img = cv2.GaussianBlur(img,(41,41),1)
    imshow(img)
    # imshow(getForegroundMask(img))
    # img = normalizeImage(img,mean,std)

    # img = clahe(img)
    # print(img.shape)
    # img = adjustGamma(img,1.2)

    # print(np.max(img))
