import logging
import logging.handlers
from pathlib import Path

class AIIntegrationLogger:
    """Centralized logging configuration for AI Integration Platform"""

    def __init__(self):
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        self.setup_logging()

    def setup_logging(self):
        """Setup comprehensive logging configuration"""

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

        # Main application log file
        app_log_file = self.log_dir / 'application.log'
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file, maxBytes=10*1024*1024, backupCount=5
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(app_handler)

        # Error log file
        error_log_file = self.log_dir / 'errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file, maxBytes=5*1024*1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)

        # Execution log file (for basket and agent executions)
        execution_log_file = self.log_dir / 'executions.log'
        execution_handler = logging.handlers.RotatingFileHandler(
            execution_log_file, maxBytes=10*1024*1024, backupCount=5
        )
        execution_handler.setLevel(logging.INFO)
        execution_handler.setFormatter(detailed_formatter)

        # Create execution logger
        execution_logger = logging.getLogger('execution')
        execution_logger.addHandler(execution_handler)
        execution_logger.setLevel(logging.INFO)
        execution_logger.propagate = False  # Don't propagate to root logger

    def get_logger(self, name: str = None):
        """Get a logger instance"""
        return logging.getLogger(name or __name__)

    def get_execution_logger(self):
        """Get the execution-specific logger"""
        return logging.getLogger('execution')

# Initialize logging system
_logging_system = AIIntegrationLogger()

# Export logger functions
def get_logger(name: str = None):
    """Get a logger instance"""
    return _logging_system.get_logger(name)

def get_execution_logger():
    """Get the execution-specific logger"""
    return _logging_system.get_execution_logger()

# Default logger for backward compatibility
logger = get_logger(__name__)