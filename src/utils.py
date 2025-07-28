import logging
import os
from datetime import datetime
import logging.handlers

def setup_logging(log_dir='logs'):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with current date
    log_filename = os.path.join(log_dir, f'job_tracker_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                log_filename,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            # Console handler
            logging.StreamHandler()
        ]
    )
    
    # Set logging levels for external libraries
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def create_directories(project_root):
    """Create necessary project directories"""
    directories = ['data', 'logs', 'backups', 'config']
    
    for directory in directories:
        dir_path = os.path.join(project_root, directory)
        os.makedirs(dir_path, exist_ok=True)

def backup_excel_file(excel_file, backup_dir='backups'):
    """Create backup of Excel file"""
    try:
        if os.path.exists(excel_file):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(excel_file)
            name, ext = os.path.splitext(filename)
            backup_filename = f"{name}_backup_{timestamp}{ext}"
            
            backup_path = os.path.join(backup_dir, backup_filename)
            os.makedirs(backup_dir, exist_ok=True)
            
            import shutil
            shutil.copy2(excel_file, backup_path)
            
            return backup_path
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating backup: {e}")
        return None



