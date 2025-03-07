import logging
from logging.handlers import RotatingFileHandler
import os

# Set the log directory and filename
log_directory = 'chatbot'
log_file = 'chatbot.logs'
log_path = os.path.join(log_directory, log_file)

def initialize_logging():
    """Configure and return a logger with rotation functionality."""
    # Create log directory if it does not exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    # Create a rotating file handler
    handler = RotatingFileHandler(
        log_path,
        maxBytes=2 * 1024 * 1024,  # Limit size to 2 MB
        backupCount=5  # Maintain up to 5 backup log files
    )
    
    # Configure logging settings
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            handler,
            logging.StreamHandler()  # Log messages to console as well
        ]
    )
    
    return logging.getLogger(__name__)

logger = initialize_logging()
