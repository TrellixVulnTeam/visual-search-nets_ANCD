import os
import json
from glob import glob
import random

import numpy as np
import joblib


def data(train_dir,
         train_size,
         gz_filename,
         val_size=None,
         test_size=None):
    """prepare training, validation, and test datasets.
    Saves a compressed Python dictionary in the path specified
    by the GZ_FILENAME option in the DATA section of a config.ini file.

    Parameters
    ----------
    train_dir : str
        path to directory where training data is saved
    train_size : int
        number of samples to put in training data set
    gz_filename : str
        name of .gz file in which to save dataset
    val_size : int
        number of samples to put in validation data set.
        Default is None, in which case there will be no validation set.
    test_size : int
        number of samples to put in test data set.
        Default is None, in which case all samples not used in training and validation sets are used for test set.

    Returns
    -------
    None

    Notes
    -----
    The dictionary saved has the following key-value pairs:
        x_train : np.ndarray
            filenames corresponding to images used as input to train neural network
        y_train : np.ndarray
            labels, expected output of neural network.
            Either element is either 1, meaning "target present", or 0, "target absent".
        x_val : np.ndarray
            filenames corresponding to images for validation set used during training
        y_val : np.ndarray
            labels for validation set
        x_test : np.ndarray
            filenames corresponding to images for set used to test accuracy of trained network
        y_test : np.ndarray
            labels for set used to test accuracy of trained network
        set_size_vec_train : np.ndarray
            "set size" of each image in x_train,
            total number of targets + distractors.
        set_size_vec_val : np.ndarray
            set size of each image in x_val
        set_size_vec_test : np.ndarray
            set size of each image in x_test
        set_sizes_by_stim : dict
            ordered set of unique set sizes, mapped to each stimulus type
            Useful if you need to plot accuracy v. set size.
        set_sizes_by_stim_stype : numpy.ndarray
        stim_type_vec_train : numpy.ndarray
            type of visual search stimulus for each image in x_train.
            Needed when there are multiple types of visual search stimuli in the dataset.
        stim_type_vec_val : numpy.ndarray
            type of visual search stimulus for each image in x_val.
        stim_type_vec_test : numpy.ndarray
            type of visual search stimulus for each image in x_test.
    """
    fname_json = glob(os.path.join(train_dir, '*.json'))

    if not fname_json:
        raise ValueError("couldn't find .json file with stimulus filenames in {}"
                         .format(train_dir))
    elif len(fname_json) > 1:
        raise ValueError("found more than one .json file with stimulus filenames in {}"
                         .format(train_dir))
    else:
        fname_json = fname_json[0]

    x_train = []
    # initialize list to convert into a
    # vector that will indicates set size
    # for each image (number of items present)
    # i.e. np.array([1, 1, 1, ..., 4, 4, 4, ... 8, 8])
    set_size_vec_train = []
    stim_type_vec_train = []
    if val_size:
        x_val = []
        set_size_vec_val = []
        stim_type_vec_val = []
    else:
        x_val = None
        set_size_vec_val = None
    x_test = []
    set_size_vec_test = []
    stim_type_vec_test = []

    with open(fname_json) as f:
        fnames_dict = json.load(f)

    num_stim_types = len(fnames_dict)  # number of keys in fnames_dict will be number of stim
    train_size_per_stim_type = train_size / num_stim_types
    if train_size_per_stim_type.is_integer():
        train_size_per_stim_type = int(train_size_per_stim_type)
    else:
        raise TypeError(f'train_size_per_stim_type, {train_size_per_stim_type}, is is not a whole number.\n'
                        'It is calculated as: (train_size / number of visual search stimulus types))\n'
                        'Adjust total number of samples, or number of stimulus types.')
    if val_size:
        val_size_per_stim_type = val_size / num_stim_types
        if val_size_per_stim_type.is_integer():
            val_size_per_stim_type=int(val_size_per_stim_type)
        else:
            raise TypeError('val_size_per_set_size is not a whole number, adjust '
                            'total number of samples, or number of set sizes.')
    else:
        val_size_per_stim_type = 0

    if test_size:
        test_size_per_stim_type = test_size / num_stim_types
        if test_size_per_stim_type.is_integer():
            test_size_per_stim_type=int(test_size_per_stim_type)
        else:
            raise TypeError('test_size_per_set_size is not a whole number, adjust '
                            'total number of samples, or number of set sizes.')
    else:
        test_size_per_stim_type = -1

    set_sizes_by_stim_stype = {}
    # below, stim type will be visual search stimulus type from searchstims package
    for stim_type, stim_info_by_set_size in fnames_dict.items():
        # and this will be set sizes declared by user for this stimulus (could be diff't for each stimulus type).
        # First have to convert set size from char to int
        stim_info_by_set_size = {int(k): v for k, v in stim_info_by_set_size.items()}

        set_sizes = [k for k in stim_info_by_set_size.keys()]
        set_sizes_by_stim_stype[stim_type] = set_sizes

        train_size_per_set_size = (train_size_per_stim_type / len(set_sizes)) / 2
        if train_size_per_set_size.is_integer():
            train_size_per_set_size = int(train_size_per_set_size)
        else:
            raise TypeError(f'train_size_per_set_size, {train_size_per_set_size}, is is not a whole number.\n'
                            'It is calculated as: (train_size_per_stim_type / len(set_sizes)) / 2\n'
                            '(2 is for target present or absent).\n'
                            'Adjust total number of samples, or number of set sizes.')
        if val_size:
            val_size_per_set_size = (val_size_per_stim_type / len(set_sizes)) / 2
            if val_size_per_set_size.is_integer():
                val_size_per_set_size = int(val_size_per_set_size)
            else:
                raise TypeError(f'val_size_per_set_size, {val_size_per_set_size},is not a whole number, adjust '
                                'total number of samples, or number of set sizes.')
        else:
            val_size_per_set_size = 0

        if test_size is None or test_size == -1:
            test_size_per_set_size = -1
        elif test_size > 0:
            test_size_per_set_size = (test_size_per_stim_type / len(set_sizes)) / 2
            if test_size_per_set_size.is_integer():
                test_size_per_set_size = int(test_size_per_set_size)
            else:
                raise TypeError(f'test_size_per_set_size, {test_size_per_set_size},is not a whole number, adjust '
                                'total number of samples, or number of set sizes.')
        else:
            raise ValueError(f'invalid test size: {test_size}')

        # the dict comprehension below contains some hard-to-comprehend unpacking
        # of 'stim_info_by_set_size', so we can just keep the filenames.
        # The structure of the .json file is a dict of dicts (see the searchstims
        # docs for more info). The net effect of the unpacking is that each
        # `present_absent_dict` is a dict with 'present' and
        # 'absent' keys. Value for each key is a list of filenames of images
        # where target is either present (if key is 'present') or absent
        stim_fnames_by_set_size = {
            set_size: {present_or_absent: [
                stim_info_dict['filename'] for stim_info_dict in stim_info_list
            ]
                for present_or_absent, stim_info_list in present_absent_dict.items()

            }
            for set_size, present_absent_dict in stim_info_by_set_size.items()
        }

        # do some extra juggling to make sure we have equal number of target present
        # and target absent stimuli for each "set size", in training and test datasets
        for set_size, stim_fnames_present_absent in stim_fnames_by_set_size.items():
            for present_or_absent, stim_fnames in stim_fnames_present_absent.items():
                total_size = sum([size
                                  for size in (train_size_per_set_size, val_size_per_set_size, test_size_per_set_size)
                                  if size is not 0 and size is not -1])
                if total_size > len(stim_fnames):
                    raise ValueError(
                        f'number of samples for training + validation set, {total_size}, '
                        f'is larger than number of samples in data set, {len(stim_fnames)}'
                    )
                stim_fnames_arr = np.asarray(stim_fnames)

                inds = list(range(len(stim_fnames)))
                random.shuffle(inds)
                train_inds = np.asarray(
                    [inds.pop() for _ in range(train_size_per_set_size)]
                )
                tmp_x_train = stim_fnames_arr[train_inds].tolist()
                x_train.extend(tmp_x_train)
                set_size_vec_train.extend([set_size] * len(tmp_x_train))
                stim_type_vec_train.extend([stim_type] * len(tmp_x_train))

                if val_size_per_set_size > 0:
                    val_inds = np.asarray(
                        [inds.pop() for _ in range(val_size_per_set_size)]
                    )
                    tmp_x_val = stim_fnames_arr[val_inds].tolist()
                    x_val.extend(tmp_x_val)
                    set_size_vec_val.extend([set_size] * len(tmp_x_val))
                    stim_type_vec_val.extend([stim_type] * len(tmp_x_val))

                if test_size_per_set_size > 0:
                    test_inds = np.asarray([inds.pop() for _ in range(test_size_per_set_size)])
                elif test_size_per_set_size == -1:
                    test_inds = np.asarray([ind for ind in inds])

                tmp_x_test = stim_fnames_arr[test_inds].tolist()
                x_test.extend(tmp_x_test)
                set_size_vec_test.extend([set_size] * len(tmp_x_test))
                stim_type_vec_train.extend([stim_type] * len(tmp_x_test))

    set_size_vec_train = np.asarray(set_size_vec_train)
    stim_type_vec_train = np.asarray(stim_type_vec_train)
    if val_size:
        set_size_vec_val = np.asarray(set_size_vec_val)
        stim_type_vec_val = np.asarray(stim_type_vec_val)
    set_size_vec_test = np.asarray(set_size_vec_test)
    stim_type_vec_test = np.asarray(stim_type_vec_test)

    y_train = np.asarray(['present' in fname for fname in x_train],
                         dtype=int)

    if val_size:
        y_val = np.asarray(['present' in fname for fname in x_val],
                           dtype=int)
    else:
        y_val = None

    y_test = np.asarray(['present' in fname for fname in x_test],
                        dtype=int)

    gz_dirname = os.path.dirname(gz_filename)
    if not os.path.isdir(gz_dirname):
        os.makedirs(gz_dirname)

    data_dict = dict(x_train=x_train,
                     y_train=y_train,
                     x_val=x_val,
                     y_val=y_val,
                     x_test=x_test,
                     y_test=y_test,
                     set_size_vec_train=set_size_vec_train,
                     set_size_vec_val=set_size_vec_val,
                     set_size_vec_test=set_size_vec_test,
                     set_sizes_by_stim_stype=set_sizes_by_stim_stype,
                     stim_type_vec_train=stim_type_vec_train,
                     stim_type_vec_val=stim_type_vec_val,
                     stim_type_vec_test=stim_type_vec_test,
                     )
    joblib.dump(data_dict, gz_filename)
