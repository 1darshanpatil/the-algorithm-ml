"""Overrides absl logger to be rank-aware for distributed pytorch usage.

    >>> # in-bazel import
    >>> from twitter.ml.logging.torch_logging import logging
    >>> # out-bazel import
    >>> from ml.logging.torch_logging import logging
    >>> logging.info(f"This only prints on rank 0 if distributed, otherwise prints normally.")
    >>> logging.info(f"This prints on all ranks if distributed, otherwise prints normally.", rank=-1)

"""
import functools
from typing import Optional

from tml.ml_logging.absl_logging import logging as logging
from absl import logging as absl_logging

import torch.distributed as dist


import functools
from typing import Optional

import torch.distributed as dist

from absl import logging as absl_logging
from tml.ml_logging.absl_logging import logging as logging


def rank_specific(logger):
    """Ensures that we only override a given logger once."""

    def _if_rank(logger_method, limit: Optional[int] = None):
        """Decorator to wrap logger_method and execute only if rank matches."""
        if limit:
            @functools.lru_cache(limit)
            def _logger_method(*args, **kwargs):
                logger_method(*args, **kwargs)
            return _logger_method

        def _inner(msg, *args, rank: int = 0, **kwargs):
            """Inner function to execute logger_method only if rank matches."""
            if not dist.is_initialized() or dist.get_rank() == rank or rank < 0:
                logger_method(msg, *args, **kwargs)

        # Register this stack frame with absl logging so that it doesn't trample logging lines.
        absl_logging.ABSLLogger.register_frame_to_skip(__file__, _inner.__name__)

        return _inner

    logger.fatal = _if_rank(logger.fatal)
    logger.error = _if_rank(logger.error)
    logger.warning = _if_rank(logger.warning, limit=1)
    logger.info = _if_rank(logger.info)
    logger.debug = _if_rank(logger.debug)
    logger.exception = _if_rank(logger.exception)

    logger._ALREADY_OVERWRITTEN_TO_BE_RANK_SPECIFIC = True

    return logger if hasattr(logger, "_ALREADY_OVERWRITTEN_TO_BE_RANK_SPECIFIC") else None


rank_specific(logging)
