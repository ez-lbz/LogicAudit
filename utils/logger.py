import logging
from rich.logging import RichHandler


def setup_logger(name: str = "audit", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = RichHandler(
            rich_tracebacks=True,
            markup= True,
            show_time=True,
            show_path=False
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    
    return logger


logger = setup_logger()
