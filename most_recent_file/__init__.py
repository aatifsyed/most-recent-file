import poetry_version
import logging


__version__ = poetry_version.extract(source_file=__file__)

logger = logging.getLogger(__name__)
