from .__about__ import (
    __author__,
    __commit__,
    __copyright__,
    __email__,
    __license__,
    __summary__,
    __title__,
    __uri__,
    __version__,
)

from . import config
from . import data
from . import datasets
from . import nets
from . import plot
from . import utils

from .learncurve import learning_curve
from .train import train
from .test import test

