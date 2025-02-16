"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""
# Implements image augmentation

import albumentations as alb
from albumentations.pytorch import ToTensorV2
import cv2
import numpy as np
from timm.data.constants import IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD


def alb_wrapper(transform):
    def f(im):
        return transform(image=np.asarray(im))["image"]

    return f


class Erosion(alb.ImageOnlyTransform):
    def __init__(self, scale, always_apply=False, p=0.5):
        super().__init__(always_apply=always_apply, p=p)
        if type(scale) is tuple or type(scale) is list:
            assert len(scale) == 2
            self.scale = scale
        else:
            self.scale = (scale, scale)

    def apply(self, img, **params):
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, tuple(np.random.randint(self.scale[0], self.scale[1], 2))
        )
        img = cv2.erode(img, kernel, iterations=1)
        return img


class Dilation(alb.ImageOnlyTransform):
    def __init__(self, scale, always_apply=False, p=0.5):
        super().__init__(always_apply=always_apply, p=p)
        if type(scale) is tuple or type(scale) is list:
            assert len(scale) == 2
            self.scale = scale
        else:
            self.scale = (scale, scale)

    def apply(self, img, **params):
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, tuple(np.random.randint(self.scale[0], self.scale[1], 2))
        )
        img = cv2.dilate(img, kernel, iterations=1)
        return img


class Bitmap(alb.ImageOnlyTransform):
    def __init__(self, value=0, lower=200, always_apply=False, p=0.5):
        super().__init__(always_apply=always_apply, p=p)
        self.lower = lower
        self.value = value

    def apply(self, img, **params):
        img = img.copy()
        img[img < self.lower] = self.value
        return img


train_transform = alb_wrapper(
    alb.Compose(
        [
            Bitmap(p=0.05),
            alb.OneOf([Erosion((2, 3)), Dilation((2, 3))], p=0.02),
            alb.Affine(shear={"x": (0, 3), "y": (-3, 0)}, cval=(255, 255, 255), p=0.03),
            alb.ShiftScaleRotate(
                shift_limit_x=(0, 0.04),
                shift_limit_y=(0, 0.03),
                scale_limit=(-0.15, 0.03),
                rotate_limit=2,
                border_mode=0,
                interpolation=2,
                value=(255, 255, 255),
                p=0.03,
            ),
            alb.GridDistortion(
                distort_limit=0.05,
                border_mode=0,
                interpolation=2,
                value=(255, 255, 255),
                p=0.04,
            ),
            alb.Compose(
                [
                    alb.Affine(
                        translate_px=(0, 5), always_apply=True, cval=(255, 255, 255)
                    ),
                    alb.ElasticTransform(
                        p=1,
                        alpha=50,
                        sigma=120 * 0.1,
                        alpha_affine=120 * 0.01,
                        border_mode=0,
                        value=(255, 255, 255),
                    ),
                ],
                p=0.04,
            ),
            alb.RandomBrightnessContrast(0.1, 0.1, True, p=0.03),
            alb.ImageCompression(95, p=0.07),
            alb.GaussNoise(20, p=0.08),
            alb.GaussianBlur((3, 3), p=0.03),
            alb.Normalize(IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD),
            ToTensorV2(),
        ]
    )
)
test_transform = alb_wrapper(
    alb.Compose(
        [
            alb.Normalize(IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD),
            ToTensorV2(),
        ]
    )
)
