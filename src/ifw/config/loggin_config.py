"""
Logging Configuration for Infraware Cloud Assistant.
Centralized logging setup with color coding and automatic file logging to ~/.ifw/logs/
"""

import logging
import logging.handlers
import warnings
import sys
import os
from pathlib import Path
from datetime import datetime


# Simple ANSI color codes
class ANSIColors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'


class ColoredFormatter(logging.Formatter):
    """Custom formatter with ANSI color coding for different log levels."""
    
    # Color mapping for log levels
    LEVEL_COLORS = {
        'DEBUG': ANSIColors.GREEN,
        'INFO': ANSIColors.BLUE,
        'WARNING': ANSIColors.YELLOW,
        'ERROR': ANSIColors.RED,
        'CRITICAL': ANSIColors.BOLD + ANSIColors.RED,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = sys.stdout.isatty()  # Only use colors for terminals
    
    def format(self, record):
        # Get the base formatted message
        message = super().format(record)
        
        if not self.use_colors:
            return message
        
        # Apply color to the entire log line
        color = self.LEVEL_COLORS.get(record.levelname, '')
        if color:
            return f"{color}{message}{ANSIColors.RESET}"
        
        return message


def setup_logging(verbose=False):
    """
    Configure logging based on verbosity level.
    
    Args:
        verbose: Enable verbose (DEBUG) logging - if True, enables DEBUG level, 
                if False, enables WARNING level (maintains original CLI behavior)
                When verbose=True, automatically saves logs to ~/.ifw/logs/log_<timestamp>.txt
    """
    
    # Determine log level (maintains original CLI behavior)
    level = logging.DEBUG if verbose else logging.WARNING
    
    # Create formatters
    detailed_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = ColoredFormatter(
        fmt='%(levelname)s | %(name)s | %(message)s'
    )
    
    formatter = detailed_formatter if verbose else simple_formatter
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with color coding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (automatic when verbose=True)
    if verbose:
        # Create ~/.ifw/logs/ directory
        home_dir = Path.home()
        ifw_dir = home_dir / '.ifw'
        logs_dir = ifw_dir / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for log filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'log_{timestamp}.txt'
        
        # Use non-colored formatter for files
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create log file handler
        file_handler = logging.FileHandler(
            filename=logs_dir / log_filename,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Always capture all levels in files
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Log the file location
        logger = logging.getLogger(__name__)
        logger.info(f"Logging to file: {logs_dir / log_filename}")
    
    # Configure third-party library loggers
    _configure_library_loggers(verbose)
    
    # Configure application loggers  
    _configure_app_loggers(level)
    
    # Handle warnings
    _configure_warnings(verbose)


def _configure_library_loggers(verbose: bool):
    """Configure logging for third-party libraries."""
    library_configs = {
        'urllib3': logging.WARNING,
        'requests': logging.WARNING,
        'boto3': logging.WARNING,
        'botocore': logging.WARNING,
        'matplotlib': logging.WARNING,
        'PIL': logging.WARNING,
        'asyncio': logging.WARNING if not verbose else logging.INFO,
        
        # Markdown processing libraries (always suppress)
        'markdown_it': logging.WARNING,
        'markdown_it.rules_block': logging.WARNING,
        'markdown_it.rules_block.heading': logging.WARNING,
        'markdown_it.rules_block.lheading': logging.WARNING,
        'markdown_it.rules_block.paragraph': logging.WARNING,
        'markdown_it.rules_block.code': logging.WARNING,
        'markdown_it.rules_block.fence': logging.WARNING,
        'markdown_it.rules_block.blockquote': logging.WARNING,
        'markdown_it.rules_block.hr': logging.WARNING,
        'markdown_it.rules_block.list': logging.WARNING,
        'markdown_it.rules_block.reference': logging.WARNING,
        'markdown_it.rules_block.html_block': logging.WARNING,
        'markdown_it.rules_inline': logging.WARNING,
        'markdown_it.rules_core': logging.WARNING,
    }
    
    for library, level in library_configs.items():
        logging.getLogger(library).setLevel(level)


def _configure_app_loggers(level: int):
    """Configure application-specific loggers."""
    app_loggers = ['strands', 'infraware', 'cloud_assistant']
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)


def _configure_warnings(verbose: bool):
    """Configure Python warnings."""
    if not verbose:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Capture warnings in logging
    logging.captureWarnings(True)
    warnings_logger = logging.getLogger('py.warnings')
    warnings_logger.setLevel(logging.WARNING if not verbose else logging.DEBUG)


if __name__ == "__main__":
    # Original CLI usage (maintains backward compatibility)
    import sys
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    setup_logging(verbose=verbose)  # This is how your CLI calls it
    
    # Test the logging with color coding
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")  # Blue
    logger.debug("Debug message")  # Green
    logger.warning("Warning message")  # Yellow
    logger.error("Error message")  # Red
    
    if verbose:
        print(f"✓ Log file saved to ~/.ifw/logs/log_<timestamp>.txt")