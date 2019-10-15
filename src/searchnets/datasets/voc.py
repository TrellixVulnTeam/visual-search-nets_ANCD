"""PyTorch Dataset class for VOC Detection task, adapted to use with Visual Search Difficulty dataset

adapted from Torchvision
https://github.com/pytorch/vision
under BSD-3 license
https://github.com/pytorch/vision/blob/master/LICENSE

VocAnnotationTransform adapted from
https://github.com/amdegroot/ssd.pytorch/blob/master/data/voc0712.py
under MIT license
https://github.com/amdegroot/ssd.pytorch/blob/master/LICENSE
"""
import collections
import os
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
from PIL import Image

from torchvision.datasets import VisionDataset
from torchvision.datasets.utils import download_url, verify_str_arg

DATASET_YEAR_DICT = {
    '2012': {
        'url': 'http://host.robots.ox.ac.uk/pascal/VOC/voc2012/VOCtrainval_11-May-2012.tar',
        'filename': 'VOCtrainval_11-May-2012.tar',
        'md5': '6cd6e144f989b92b3379bac3b3de84fd',
        'base_dir': 'VOCdevkit/VOC2012'
    },
    '2011': {
        'url': 'http://host.robots.ox.ac.uk/pascal/VOC/voc2011/VOCtrainval_25-May-2011.tar',
        'filename': 'VOCtrainval_25-May-2011.tar',
        'md5': '6c3384ef61512963050cb5d687e5bf1e',
        'base_dir': 'TrainVal/VOCdevkit/VOC2011'
    },
    '2010': {
        'url': 'http://host.robots.ox.ac.uk/pascal/VOC/voc2010/VOCtrainval_03-May-2010.tar',
        'filename': 'VOCtrainval_03-May-2010.tar',
        'md5': 'da459979d0c395079b5c75ee67908abb',
        'base_dir': 'VOCdevkit/VOC2010'
    },
    '2009': {
        'url': 'http://host.robots.ox.ac.uk/pascal/VOC/voc2009/VOCtrainval_11-May-2009.tar',
        'filename': 'VOCtrainval_11-May-2009.tar',
        'md5': '59065e4b188729180974ef6572f6a212',
        'base_dir': 'VOCdevkit/VOC2009'
    },
    '2008': {
        'url': 'http://host.robots.ox.ac.uk/pascal/VOC/voc2008/VOCtrainval_14-Jul-2008.tar',
        'filename': 'VOCtrainval_11-May-2012.tar',
        'md5': '2629fa636546599198acfcfbfcf1904a',
        'base_dir': 'VOCdevkit/VOC2008'
    },
    '2007': {
        'url': 'http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtrainval_06-Nov-2007.tar',
        'filename': 'VOCtrainval_06-Nov-2007.tar',
        'md5': 'c52e279531787c972589f7e41ab4ae64',
        'base_dir': 'VOCdevkit/VOC2007'
    }
}


class VOCDetection(VisionDataset):
    """`Pascal VOC <http://host.robots.ox.ac.uk/pascal/VOC/>`_ Detection Dataset.
    Modified
    """
    def __init__(self,
                 root,
                 csv_file,
                 split='train',
                 year='2012',
                 image_set='train',
                 download=False,
                 transform=None,
                 target_transform=None,
                 transforms=None,
                 return_img_name=False):
        """
        Parameters
        ----------
        root (string): Root directory of the VOC Dataset.
        year (string, optional): The dataset year, supports years 2007 to 2012.
        image_set (string, optional): Select the image_set to use, ``train``, ``trainval`` or ``val``
        download (bool, optional): If true, downloads the dataset from the internet and
            puts it in root directory. If dataset is already downloaded, it is not
            downloaded again.
            (default: alphabetic indexing of VOC's 20 classes).
        transform (callable, optional): A function/transform that  takes in an PIL image
            and returns a transformed version. E.g, ``transforms.RandomCrop``
        target_transform (callable, optional): A function/transform that takes in the
            target and transforms it.
        transforms (callable, optional): A function/transform that takes input sample and its target as entry
            and returns a transformed version.
        return_img_name : bool
            if True, return image name (without extension, i.e. 'stem' of filename). Used with test set,
            in order to correlate accuracy on a given image with its Visual Search Difficulty score.
        """
        super(VOCDetection, self).__init__(root, transforms, transform, target_transform)
        self.year = year
        self.url = DATASET_YEAR_DICT[year]['url']
        self.filename = DATASET_YEAR_DICT[year]['filename']
        self.md5 = DATASET_YEAR_DICT[year]['md5']
        valid_sets = ["train", "trainval", "val"]
        if year == "2007":
            valid_sets.append("test")
        self.image_set = verify_str_arg(image_set, "image_set", valid_sets)

        # csv file generated by searchnets.data.split
        # get now so we can use below to only keep images and annotations from the split specified
        self.csv_file = csv_file
        self.split = split
        df = pd.read_csv(csv_file)
        df = df[df['split'] == split]
        self.df = df

        base_dir = DATASET_YEAR_DICT[year]['base_dir']
        voc_root = os.path.join(self.root, base_dir)
        image_dir = os.path.join(voc_root, 'JPEGImages')
        annotation_dir = os.path.join(voc_root, 'Annotations')

        if download:
            download_extract(self.url, self.root, self.filename, self.md5)

        if not os.path.isdir(voc_root):
            raise RuntimeError('Dataset not found or corrupted.' +
                               ' You can use download=True to download it')

        splits_dir = os.path.join(voc_root, 'ImageSets/Main')
        split_f = os.path.join(splits_dir, image_set.rstrip('\n') + '.txt')
        with open(os.path.join(split_f), "r") as f:
            file_names = [x.strip() for x in f.readlines()]
        self.images = []
        self.annotations = []
        for file_name in file_names:
            if np.any(df['img'].isin([file_name])):
                self.images.append(os.path.join(image_dir, file_name + ".jpg"))
                self.annotations.append(os.path.join(annotation_dir, file_name + ".xml"))
        assert (len(self.images) == len(self.annotations))

        self.return_img_name = return_img_name

    def __getitem__(self, index):
        """
        Parameters
        ----------
        index : int
            index of training sample in dataset

        Returns
        -------
        image : torch.Tensor
            image as a tensor
        target : torch.Tensor
            one-hot encoding of what objects are present in the image.
        img_name : str
            file name without extension. Only returned if return_img_name attribute is set to True.
        """
        img_path = self.images[index]
        img = Image.open(img_path).convert('RGB')
        target = self.parse_voc_xml(
            ET.parse(self.annotations[index]).getroot())
        img, target = self.transforms(img, target)  # will be VOCTransform
        if self.return_img_name:
            return img, target, Path(img_path).stem
        else:
            return img, target

    def __len__(self):
        return len(self.images)

    @staticmethod
    def parse_voc_xml(node):
        voc_dict = {}
        children = list(node)
        if children:
            def_dic = collections.defaultdict(list)
            for dc in map(VOCDetection.parse_voc_xml, children):
                for ind, v in dc.items():
                    def_dic[ind].append(v)
            voc_dict = {
                node.tag:
                    {ind: v[0] if len(v) == 1 else v
                     for ind, v in def_dic.items()}
            }
        if node.text:
            text = node.text.strip()
            if not children:
                voc_dict[node.tag] = text
        return voc_dict


def download_extract(url, root, filename, md5):
    download_url(url, root, filename, md5)
    with tarfile.open(os.path.join(root, filename), "r") as tar:
        tar.extractall(path=root)
