import os
import sys

from loguru import logger

# Make sure the logs folder exists before Loguru tries to write to it
os.makedirs("logs", exist_ok=True)

# Remove Loguru's default handler so we control formatting ourselves
logger.remove()

# Console output — useful while developing (visible in your terminal)
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | {message}"
)

# File output — rotates daily, keeps 7 days, compresses old logs
logger.add(
    "logs/app.log",
    level="INFO",
    rotation="00:00",
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}"
)