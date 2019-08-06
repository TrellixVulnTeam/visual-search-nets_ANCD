"""functions for computing metrics: error, probabilities, etc."""
import numpy as np
from scipy.stats import norm


z_score = norm.ppf


def compute_d_prime(y_true, y_pred):
    """computes d prime given y_true and y_pred

    adapted from <https://lindeloev.net/calculating-d-in-python-and-php/>
    """
    hits = np.logical_and(y_pred == 1, y_true == 1).sum()
    misses = np.logical_and(y_pred == 0, y_true == 1).sum()
    hit_rate = hits / (hits + misses)

    false_alarms = np.logical_and(y_pred == 1, y_true == 0).sum()
    correct_rejects = np.logical_and(y_pred == 0, y_true == 0).sum()
    false_alarm_rate = false_alarms / (false_alarms + correct_rejects)

    # standard correction to avoid d' value of infinity or minus infinity;
    # if either is 0 or 1, assume "true" value is somewhere between 0 (or 1)
    # and (1/2N) where N is the number of targets (or "lures", as appropriate)
    half_hit = 0.5 / (hits + misses)
    half_fa = 0.5 / (false_alarms + correct_rejects)

    if hit_rate == 1:
        hit_rate = 1 - half_hit
    if hit_rate == 0:
        hit_rate = half_hit

    if false_alarm_rate == 1:
        false_alarm_rate = 1 - half_fa
    if false_alarm_rate == 0:
        false_alarm_rate = half_fa

    d_prime = z_score(hit_rate) - z_score(false_alarm_rate)
    return hit_rate.item(), false_alarm_rate.item(), d_prime.item()


def p_item_grid(char_grids, item_char='t', return_counts=False):
    """compute probability that item appears within each cell of grid

    Parameters
    ----------
    char_grids : list
        of lists or numpy.ndarrays, each representing a visual search stimulus
        as a grid of characters, where the character in each cell corresponds
        to some item type that can appear in the visual search stimulus.
        The searchstims library saves such a representation of each stimulus it
        generates in the .json metadata file that it saves.
    item_char : str
        Character that represents item for which probability should be computed.
        Default is 't' (for 'target').
    return_counts : bool
        if True, return array with count of number of occurrences of item_char in
        each cell. Default is False.

    Returns
    -------
    p : numpy.ndarray
        of same shape as char_grids, where value of each element is probability
        that item_char occurs in the corresponding cell in char_grids
    counts : numpy.ndarray
        counts used to compute p (by dividing by np.sum(counts)).
        Only returned if return_counts is True
    """
    char_grids = [np.asarray(g) for g in char_grids]

    grid_shape = [g.shape for g in char_grids]
    grid_shape = set(grid_shape)
    if len(grid_shape) == 1:
        grid_shape = grid_shape.pop()
    else:
        raise ValueError(
            'found more than one shape for visual search stimuli grids: '
            f'{grid_shape}'
        )

    counts = np.zeros(grid_shape)
    for g in char_grids:
        # increment by 1 the cell where the item type is found
        # using indices returned by np.nonzero
        counts[np.nonzero(g == item_char)] += 1
    p = counts / np.sum(counts)
    if return_counts:
        return p, counts
    else:
        return p


def acc_grid(stim_fnames, y_true, y_pred, char_grids, stim_fnames_meta, return_counts=False):
    """compute accuracy for each cell of grid in visual search stimulus

    Parameters
    ----------
    stim_fnames : list
    y_true : numpy.ndarray
    y_pred : numpy.ndarray
    char_grids : list
        of lists or numpy.ndarrays, each representing a visual search stimulus
        as a grid of characters, where the character in each cell corresponds
        to some item type that can appear in the visual search stimulus.
        The searchstims library saves such a representation of each stimulus it
        generates in the .json metadata file that it saves.
    stim_fnames_meta : list
    return_counts : bool
        if True, return array with count of number of occurrences of item_char in
        each cell. Default is False.

    Returns
    -------
    acc : numpy.ndarray
        of same shape as char_grids, where value of each element is probability
        that item_char occurs in the corresponding cell in char_grids
    counts : numpy.ndarray
        counts used to compute p (by dividing by np.sum(counts)).
        Only returned if return_counts is True
    """
    # convert to numpy.ndarray so we can use np.nonzero, check for multiple occurrences (not that we want to find them)
    stim_fnames = np.asarray(stim_fnames)
    stim_fnames_meta = np.asarray(stim_fnames_meta)

    char_grids = [np.asarray(g) for g in char_grids]

    grid_shape = [g.shape for g in char_grids]
    grid_shape = set(grid_shape)
    if len(grid_shape) == 1:
        grid_shape = grid_shape.pop()
    else:
        raise ValueError(
            'found more than one shape for visual search stimuli grids: '
            f'{grid_shape}'
        )

    correct_counts = np.zeros(grid_shape)
    trial_counts = np.zeros(grid_shape)
    for g, g_fname in zip(char_grids, stim_fnames_meta):
        # get indices in character grid that are not empty
        row_inds, col_inds = np.nonzero(g != '')

        # find index of filename that corresponds to grid in
        # list of filenames that corresponds to y_true and y_pred
        ind = np.nonzero(stim_fnames == g_fname)[0]
        if ind.shape[0] != 1:
            raise ValueError(
                f'Did not find only one index for {g_fname} in list of stimulus filenames made by searchnets.data.\n'
                f'Indices found were: {ind}'
            )
        ind = ind[0]

        is_correct = (y_true[ind] == y_pred[ind])
        if is_correct:
            for row_ind, col_ind in zip(row_inds, col_inds):
                correct_counts[row_ind, col_ind] += 1
        for row_ind, col_ind in zip(row_inds, col_inds):
            trial_counts[row_ind, col_ind] += 1

    acc = correct_counts / trial_counts
    if return_counts:
        return acc, correct_counts, trial_counts
    else:
        return acc


def err_grid(stim_fnames, y_true, y_pred, char_grids, stim_fnames_meta, return_counts=False):
    if return_counts:
        acc, correct_counts, trial_counts = acc_grid(
            stim_fnames, y_true, y_pred, char_grids, stim_fnames_meta, return_counts
        )
    else:
        acc = acc_grid(stim_fnames, y_true, y_pred, char_grids, stim_fnames_meta, return_counts)

    err = 1 - acc

    if return_counts:
        return err, correct_counts, trial_counts
    else:
        return err
