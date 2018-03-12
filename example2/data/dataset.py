import torch as t
from .voc_dataset import VOCBboxDataset
from skimage import transform as sktsf
from torchvision import transforms as tvtsf
from . import util
import numpy as np
from utils.config import opt

# 不考虑使用 caffe 预训练模型， caffe相关部分都被删掉了

def inverse_normalize(img):
    # approximate un-normalize for visualize
    return (img * 0.225 + 0.45).clip(min=0, max=1) * 255


def pytorch_normalize(img):
    """
    https://github.com/pytorch/vision/issues/223
    return appr -1~1 RGB
    """
    normalize = tvtsf.Normalize(mean = [0.485, 0.456, 0.406],
                                std  = [0.229, 0.224, 0.225])
    img = normalize(t.from_numpy(img))
    return img.numpy()


def preprocess(img, min_size=600, max_size=1000):
    """Preprocess an image for feature extraction.
    """
    C, H, W = img.shape
#    scale1 = min_size / min(H, W)
#    scale2 = max_size / max(H, W)
#    scale = min(scale1, scale2)
    
    duan_bian = min(H,W)
    if duan_bian < min_size:
        scale = min_size / duan_bian 
        # 如果图片较短的边比 min_size 还小，则将短边拉升到 min_size，否则不scale，保持原图大小
        # max_size 在这里没用到
    else:
        scale = 1.0
    
    img = img / 255.
    img = sktsf.resize(img, (C, H * scale, W * scale), mode='reflect')
 
    return pytorch_normalize(img) # 不考虑caffe_normalize


class Transform(object):
    def __init__(self, min_size=600, max_size=1000):
        self.min_size = min_size
        self.max_size = max_size

    def __call__(self, in_data):
        img, bbox, label = in_data
        _, H, W = img.shape
        img = preprocess(img, self.min_size, self.max_size)
        _, o_H, o_W = img.shape
        scale = o_H / H
        bbox = util.resize_bbox(bbox, (H, W), (o_H, o_W))

        # horizontally flip
        img, params = util.random_flip(img, x_random=True, return_param=True)
        bbox = util.flip_bbox(bbox, (o_H, o_W), x_flip=params['x_flip'])

        return img, bbox, label, scale


class Dataset:
    def __init__(self, opt):
        self.opt = opt
        self.db = VOCBboxDataset(opt.voc_data_dir)
        self.tsf = Transform(opt.min_size, opt.max_size)

    def __getitem__(self, idx):
        ori_img, bbox, label, difficult = self.db.get_example(idx)

        img, bbox, label, scale = self.tsf((ori_img, bbox, label))
        return img.copy(), bbox.copy(), label.copy(), scale

    def __len__(self):
        return len(self.db)


class TestDataset:
    def __init__(self, opt, split='test', use_difficult=True):
        self.opt = opt
        self.db = VOCBboxDataset(opt.test_data_dir, split=split, use_difficult=use_difficult)

    def __getitem__(self, idx):
        ori_img, bbox, label, difficult = self.db.get_example(idx)
        img = preprocess(ori_img)
        return img, ori_img.shape[1:], bbox, label, difficult

    def __len__(self):
        return len(self.db)
