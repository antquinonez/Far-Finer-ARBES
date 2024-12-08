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
        directory = os.path.dirname(default_name)
        base_filename = os.path.basename(self.baseFilename)
        name, ext = os.path.splitext(base_filename)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(directory, f"{name}_{timestamp}{ext}")
    
    def _rotator(self, source, dest):
        """Handle the file rotation and cleanup"""
        if os.path.exists(source):
            os.rename(source, dest)
        
        self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        """Delete oldest files when we exceed max_files"""
        directory = os.path.dirname(self.baseFilename)
        base_filename = os.path.basename(self.baseFilename)
        name, ext = os.path.splitext(base_filename)
        
        pattern = os.path.join(directory, f"{name}_*{ext}")
        files = glob.glob(pattern)
        
        files.sort(key=os.path.getmtime)
        
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
    max_files=20,
    logger_name=None
):
    """
    Configure logging with detailed formatting and timed rotating file output.
    
    Args:
        log_file (str, optional): Path to log file. If None, logs to console only.
        log_level (int, optional): Logging level. Defaults to DEBUG.
        log_format (str, optional): Custom log format string. If None, uses default format.
        max_files (int, optional): Maximum number of backup files to keep. Defaults to 20.
        logger_name (str, optional): Name for the logger. If None, uses root logger.
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

    # Create a named logger instead of using root logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove any existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Timed rotating file handler
    if log_file:
        # Add timestamp to the log filename
        log_dir = os.path.dirname(log_file)
        base_name, ext = os.path.splitext(os.path.basename(log_file))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamped_filename = f"{base_name}_{timestamp}{ext}"
        full_log_path = os.path.join(log_dir, timestamped_filename)
        
        # Create directory if it doesn't exist
        log_path = Path(full_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = CustomTimedRotatingFileHandler(
            full_log_path,
            max_files=max_files,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to parent loggers
    logger.propagate = False
    
    return logger