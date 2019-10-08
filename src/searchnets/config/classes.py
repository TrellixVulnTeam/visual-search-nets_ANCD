""" classes to represent sections of config.ini file """
import attr
from attr.validators import instance_of, optional


def is_pos_int(instance, attribute, value):
    if type(value) != int:
        raise ValueError(
            f'type of {attribute.name} must be an int'
        )
    if value < 1:
        raise ValueError(
            f'{attribute.name} must be a positive integer, but was: {value}'
        )


def is_non_neg_int(instance, attribute, value):
    if type(value) != int:
        raise ValueError(
            f'type of {attribute.name} must be an int'
        )
    if value < 0:
        raise ValueError(
            f'{attribute.name} must be a non-negative integer, but was: {value}'
        )


@attr.s
class TrainConfig:
    """class to represent [TRAIN] section of config.ini file

    Attributes
    ----------
    net_name : str
        name of convolutional neural net architecture to train.
        One of {'alexnet', 'VGG16'}
    number_nets_to_train : int
        number of training "replicates"
    new_learn_rate_layers : list
        of layer names whose weights will be initialized randomly
        and then trained with the 'new_layer_learning_rate'.
    new_layer_learning_rate : float
        Applied to `new_learn_rate_layers'. Should be larger than
        `base_learning_rate` but still smaller than the usual
        learning rate for a deep net trained with SGD,
        e.g. 0.001 instead of 0.01
    epochs_list : list
        of training epochs. Replicates will be trained for each
        value in this list. Can also just be one value, but a list
        is useful if you want to test whether effects depend on
        number of training epochs.
    batch_size : int
        number of samples in a batch of training data
    random_seed : int
        to seed random number generator
    save_path : str
        path to directory where model and any checkpoints should be saved
    base_learning_rate : float
        Applied to layers with weights loaded from training the
        architecture on ImageNet. Should be a very small number
        so the trained weights don't change much. Default is 0.0
    freeze_trained_weights : bool
        if True, freeze weights in any layer not in "new_learn_rate_layers".
        These are the layers that have weights pre-trained on ImageNet.
        Default is False. Done by simply not applying gradients to these weights,
        i.e. this will ignore a base_learning_rate if you set it to something besides zero.
    dropout_rate : float
        Probability that any unit in a layer will "drop out" during
        a training epoch, as a form of regularization. Default is 0.5.
    loss_func : str
        type of loss function to use. One of {'CE', 'invDPrime'}. Default is 'CE',
        the standard cross-entropy loss. 'invDprime' is inverse D prime.
    optimizer : str
        optimizer to use. One of {'SGD', 'Adam', 'AdamW'}.
    triplet_loss_margin : float
        Minimum margin between clusters, parameter in triplet loss function. Default is 0.5.
    squared_dist : bool
        if True, when computing similarity of embeddings (e.g. for triplet loss), use pairwise squared
        distance, i.e. Euclidean distance.
    save_acc_by_set_size_by_epoch : bool
        if True, compute accuracy on training set for each epoch separately
        for each unique set size in the visual search stimuli. These values
        are saved in a matrix where rows are epochs and columns are set sizes.
        Useful for seeing whether accuracy converges for each individual
        set size. Default is False.
    use_val : bool
        if True, use validation set.
    val_epoch : int
        if not None, accuracy on validation set will be measured every `val_epoch` epochs
    summary_step : int
        Step on which to write summaries to file. Each minibatch is counted as one step, and steps are counted across
        epochs. Default is None.
    patience : int
        if not None, training will stop if accuracy on validation set has not improved in `patience` steps
    checkpoint_epoch : int
        if not None, a checkpoint will be saved every `checkpoint_epoch` epochs. Default is None.
    num_workers : int
        number of workers used by torch.DataLoaders. Default is 4.
    data_parallel : bool
        if True, use torch.nn.DataParallel to train model across multiple GPUs. Default is False.        
    """
    net_name = attr.ib(validator=instance_of(str))
    number_nets_to_train = attr.ib(validator=instance_of(int))
    epochs_list = attr.ib(validator=instance_of(list))
    @epochs_list.validator
    def check_epochs_list(self, attribute, value):
        for ind, epochs in enumerate(value):
            if type(epochs) != int:
                raise TypeError('all values in epochs_list should be int but '
                                f'got type {type(epochs)} for element {ind}')

    batch_size = attr.ib(validator=instance_of(int))
    random_seed = attr.ib(validator=instance_of(int))
    save_path = attr.ib(validator=instance_of(str))

    # ------------------------ have defaults ------------------------------------------------
    method = attr.ib(validator=instance_of(str), default='transfer')
    @method.validator
    def check_method(self, attribute, value):
        if value not in {'initialize', 'transfer'}:
            raise ValueError(
                f"method must be one of {{'initialize', 'transfer'}}, but was {value}."
            )
    # for 'initialize' training
    learning_rate = attr.ib(validator=instance_of(float), default=0.001)

    # for 'transfer' training
    new_learn_rate_layers = attr.ib(validator=instance_of(list), default=['fc8'])
    @new_learn_rate_layers.validator
    def check_new_learn_rate_layers(self, attribute, value):
        for layer_name in value:
            if type(layer_name) != str:
                raise TypeError(f'new_learn_rate_layer names should be strings but got {layer_name}')
    new_layer_learning_rate = attr.ib(validator=instance_of(float), default=0.001)
    base_learning_rate = attr.ib(validator=instance_of(float), default=1e-20)
    freeze_trained_weights = attr.ib(validator=instance_of(bool), default=True)

    loss_func = attr.ib(validator=instance_of(str), default='CE')
    @loss_func.validator
    def check_loss_func(self, attribute, value):
        if value not in {'CE', 'InvDPrime', 'triplet', 'triplet-CE'}:
            raise ValueError(
                f"loss_func must be one of {{'CE', 'InvDPrime', 'triplet', 'triplet-CE'}}, but was {value}."
            )
    optimizer = attr.ib(validator=instance_of(str), default='SGD')
    @optimizer.validator
    def check_optimizer(self, attribute, value):
        if value not in {'SGD', 'Adam', 'AdamW'}:
            raise ValueError(
                f"loss_func must be one of {{'SGD', 'Adam', 'AdamW'}}, but was {value}."
            )

    save_acc_by_set_size_by_epoch = attr.ib(validator=instance_of(bool), default=False)
    use_val = attr.ib(validator=instance_of(bool), default=False)
    val_epoch = attr.ib(validator=optional(is_pos_int), default=None)
    summary_step = attr.ib(validator=optional(is_pos_int), default=None)
    patience = attr.ib(validator=optional(is_pos_int), default=None)
    checkpoint_epoch = attr.ib(validator=optional(is_pos_int), default=None)
    num_workers = attr.ib(validator=optional(is_non_neg_int), default=4)
    data_parallel = attr.ib(validator=optional(instance_of(bool)), default=False)


def is_list_of_pos_int(instance, attribute, value):
    if type(value) != list:
        raise ValueError(
            f'type of {attribute.name} must be a list'
        )

    for ind, item in enumerate(value):
        if type(item) != int:
            raise ValueError(
                f'all elements in {attribute.name} must be int but item at index {ind} was: {type(item)}'
            )
        if item < 1:
            raise ValueError(
                f'all elements in {attribute.name} must be positive integer, but item at index {ind} was: {item}'
            )


def is_list_of_str(instance, attribute, value):
    if type(value) != list:
        raise ValueError(
            f'type of {attribute.name} must be a list'
        )

    for ind, item in enumerate(value):
        if type(item) != str:
            raise ValueError(
                f'all elements in {attribute.name} must be str but item at index {ind} was: {type(item)}'
            )


@attr.s
class DataConfig:
    """class to represent [DATA] section of config.ini file

    Attributes
    ----------
    csv_file_in : str
        path to .csv file generated by searchstims package. Typically in root of train_dir.
    train_size : integer
        Number of images to include in training set.
    csv_file_out : str
        name of .csv file generated by searchnets.data.split.
    stim_types : list
        of strings; specifies which visual search stimulus types to use when creating dataset. Strings must be keys in
        .json file within train_dir. Default is None, in which case all types found in .csv file will be used.
    val_size : integer
        Number of images to include in validation set. Used after each epoch to estimate accuracy of trained network.
        Default is None.
    set_sizes : list
        Specifies the 'set size' of the visual search stimuli.  The set size is the total number of targets and
        distractors, AKA "items", in a visual search stimulus. Set sizes will already have been specified when
        creating the images with `searchstims`, but here the user can choose to use all or only some of the available
        set sizes. Images for each set size are saved in separate folders by `searchstims`, so this list will be used
        to find the paths to those folders within `TRAIN_DIR`.
    train_size_per_set_size, val_size_per_set_size, test_size_per_set_size : list
        number of samples in split per visual search set size. Default is None, in which case the total number of
        samples for each stimulus type will be divided by the number of set sizes, so that an equal number is used
        for each set size.
    """
    csv_file_in = attr.ib(validator=instance_of(str))
    train_size = attr.ib(validator=instance_of(int))
    csv_file_out = attr.ib(validator=optional(instance_of(str)), default=None)
    stim_types = attr.ib(validator=optional(is_list_of_str), default=None)
    val_size = attr.ib(validator=optional(instance_of(int)), default=None)
    test_size = attr.ib(validator=optional(instance_of(int)), default=None)
    set_sizes = attr.ib(validator=instance_of(list), default=None)

    @set_sizes.validator
    def check_set_sizes(self, attribute, value):
        for ind, set_size in enumerate(value):
            if type(set_size) != int:
                raise TypeError('all values in set_sizes should be int but '
                                f'got type {type(set_size)} for element {ind}')

    train_size_per_set_size = attr.ib(validator=optional(is_list_of_pos_int), default=None)
    val_size_per_set_size = attr.ib(validator=optional(is_list_of_pos_int), default=None)
    test_size_per_set_size = attr.ib(validator=optional(is_list_of_pos_int), default=None)

    def __attrs_post_init__(self):
        if self.csv_file_out is None:
            self.csv_file_out = self.csv_file_in + '_split.csv'


@attr.s
class TestConfig:
    """class to represent [TEST] section of config.ini file

    Attributes
    ----------
    test_results_save_path : string
        Path to directory where results of measuring accuracy on a test set should be saved.
    """
    test_results_save_path = attr.ib(validator=instance_of(str))


@attr.s
class LearnCurveConfig:
    """class to represent [LEARNCURVE] section of config.ini file

    Attributes
    ----------
    train_size_list : list
        of ints, sizes of training sets used to generate learning curve
    """
    train_size_list = attr.ib(validator=instance_of(list))

    @train_size_list.validator
    def check_train_size_list(self, attribute, value):
        for ind, train_size in enumerate(value):
            if type(train_size) != int:
                raise TypeError('all values in train_size_list should be int but '
                                f'got type {type(train_size)} for element {ind}')


@attr.s
class Config:
    """class to represent all sections of config.ini file

    Attributes
    ----------
    train: TrainConfig
        represents [TRAIN] section
    data: DataConfig
        represents [DATA] section
    test: TestConfig
        represents [TEST] section
    learncurve: LearnCurveConfig
        represents [LEARNCURVE] section
    """
    train = attr.ib(validator=instance_of(TrainConfig))
    data = attr.ib(validator=instance_of(DataConfig))
    test = attr.ib(validator=instance_of(TestConfig))
    learncurve = attr.ib(validator=optional(instance_of(LearnCurveConfig)), default=None)
