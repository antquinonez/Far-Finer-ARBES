import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import glob

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Custom handler that uses datetime in backup filenames and manages file count"""
    
    def __init__(self, filename, max_files=20, **kwargs):
        super().__init__(filename, when='midnight', interval=1, **kwargs)
        self.max_files = max_files
        self.namer = self._namer
        self.rotator = self._rotator
        
    def _namer(self, default_name):
        """Generate backup filename with datetime instead of count"""
        # Extract the base directory and filename
        directory = os.path.dirname(default_name)
        base_filename = os.path.basename(self.baseFilename)
        name, ext = os.path.splitext(base_filename)
        
        # Create new filename with current datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(directory, f"{name}_{timestamp}{ext}")
    
    def _rotator(self, source, dest):
        """Handle the file rotation and cleanup"""
        # Rename the current file
        if os.path.exists(source):
            os.rename(source, dest)
        
        # Cleanup old files if we have too many
        self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        """Delete oldest files when we exceed max_files"""
        directory = os.path.dirname(self.baseFilename)
        base_filename = os.path.basename(self.baseFilename)
        name, ext = os.path.splitext(base_filename)
        
        # Get all matching log files
        pattern = os.path.join(directory, f"{name}_*{ext}")
        files = glob.glob(pattern)
        
        # Sort files by modification time (oldest first)
        files.sort(key=os.path.getmtime)
        
        # Remove oldest files if we exceed max_files
        while len(files) >= self.max_files:
            oldest_file = files.pop(0)
            try:
                os.remove(oldest_file)
                logging.debug(f"Deleted old log file: {oldest_file}")
            except OSError as e:
                logging.error(f"Error deleting {oldest_file}: {e}")

def setup_logging(
    log_file=None,
    log_level=logging.DEBUG,
    log_format=None,
    max_files=20
):
    """
    Configure logging with detailed formatting and timed rotating file output.
    
    Args:
        log_file (str, optional): Path to log file. If None, logs to console only.
        log_level (int, optional): Logging level. Defaults to DEBUG.
        log_format (str, optional): Custom log format string. If None, uses default format.
        max_files (int, optional): Maximum number of backup files to keep. Defaults to 20.
    """
    if log_format is None:
        log_format = (
            '%(asctime)s | %(levelname)-8s | '
            '%(filename)s:%(lineno)d | '
            '%(funcName)s | '
            '%(message)s'
        )

    formatter = logging.Formatter(
        log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Timed rotating file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = CustomTimedRotatingFileHandler(
            log_file,
            max_files=max_files,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# # Example usage
# if __name__ == "__main__":
#     log_file = "logs/app.log"
#     logger = setup_logging(log_file=log_file, max_files=20)
    
#     # Example log messages
#     logger.debug("Debug message")
#     logger.info("Info message")
#     logger.warning("Warning message")
#     logger.error("Error message")
#     logger.critical("Critical message")
    
#     # Example with exception
#     try:
#         1/0
#     except Exception as e:
#         logger.exception("An error occurred")