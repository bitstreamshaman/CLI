"""
Logging Configuration for Infraware Cloud Assistant.
Centralized logging setup and configuration.
"""
import logging
import warnings

def setup_logging(verbose=False):
    """Configure logging based on verbosity level."""
    # Set the base logging level
    level = logging.DEBUG if verbose else logging.WARNING
    
    # Configure the root logger
    logging.basicConfig(
        level=level,
        format="%(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler()]
    )

    # Only show warnings in verbose mode
    if not verbose:
        warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Configure the strands logger specifically
    strands_logger = logging.getLogger("strands")
    strands_logger.setLevel(logging.DEBUG if verbose else logging.WARNING)
