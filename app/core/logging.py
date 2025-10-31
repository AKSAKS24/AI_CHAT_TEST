import os, sys
from loguru import logger
from app.core.config import settings

def configure_logging():
    logger.remove()
    fmt = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    logger.add(sys.stdout, level=settings.LOG_LEVEL, format=fmt, enqueue=True, backtrace=False, diagnose=False)
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    logger.add(os.path.join(log_dir, "app.log"), rotation="10 MB", retention="10 days", level=settings.LOG_LEVEL, format=fmt, enqueue=True)
    logger.info("Logging configured")
