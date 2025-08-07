# PrintSmart Job Timeout Configuration
# This file defines timeout settings for different job states

# Default timeout settings (in minutes)
DEFAULT_TIMEOUTS = {
    # How long a job can stay in 'pending' status before expiring
    'PENDING_TIMEOUT': 30,
    
    # How long a job can stay in 'processing' or 'printing' before being considered stuck
    'PROCESSING_TIMEOUT': 60,
    
    # How old jobs must be before they're considered abandoned (in days)
    'ABANDONED_THRESHOLD': 7,
    
    # Enable automatic refunds for expired jobs
    'AUTO_REFUND_ENABLED': True,
    
    # Enable user notifications for expired jobs
    'NOTIFY_USERS': True,
    
    # Retry failed jobs when printers come back online
    'AUTO_RETRY_ON_RECOVERY': True,
}

# Environment-specific overrides
DEVELOPMENT_TIMEOUTS = {
    'PENDING_TIMEOUT': 5,      # Shorter timeouts for testing
    'PROCESSING_TIMEOUT': 10,
}

PRODUCTION_TIMEOUTS = {
    'PENDING_TIMEOUT': 60,     # Longer timeouts for production
    'PROCESSING_TIMEOUT': 120,
    'ABANDONED_THRESHOLD': 14, # Keep records longer in production
}

# Job priority timeout modifiers
# Higher priority jobs get longer timeouts
PRIORITY_MODIFIERS = {
    1: 0.5,   # Urgent jobs: 50% of normal timeout
    2: 0.7,   # High priority: 70% of normal timeout  
    3: 0.9,   # Above normal: 90% of normal timeout
    4: 1.0,   # Normal: 100% of normal timeout
    5: 1.0,   # Default: 100% of normal timeout
    6: 1.2,   # Below normal: 120% of normal timeout
    7: 1.5,   # Low priority: 150% of normal timeout
    8: 2.0,   # Very low: 200% of normal timeout
    9: 3.0,   # Bulk jobs: 300% of normal timeout
    10: 5.0,  # Background: 500% of normal timeout
}

# File type timeout modifiers
# Larger/complex files get longer timeouts
FILE_TYPE_MODIFIERS = {
    'pdf': 1.0,      # Standard timeout
    'docx': 1.2,     # 20% longer for document processing
    'xlsx': 1.5,     # 50% longer for spreadsheets
    'pptx': 1.3,     # 30% longer for presentations
    'jpg': 0.8,      # 20% shorter for simple images
    'png': 0.8,      # 20% shorter for simple images
    'txt': 0.5,      # 50% shorter for text files
}

# Printer type timeout modifiers
# Different printer types have different processing speeds
PRINTER_TYPE_MODIFIERS = {
    'laser': 1.0,        # Standard timeout
    'inkjet': 1.5,       # 50% longer for inkjet
    'thermal': 0.8,      # 20% shorter for thermal
    'dot_matrix': 2.0,   # 100% longer for dot matrix
}

# Retry configuration for expired jobs
RETRY_CONFIG = {
    'MAX_RETRIES': 3,
    'RETRY_DELAYS': [5, 15, 30],  # Minutes to wait between retries
    'EXPONENTIAL_BACKOFF': True,
}

# Notification configuration
NOTIFICATION_CONFIG = {
    'SEND_EMAIL': True,
    'SEND_PUSH': False,
    'SEND_SMS': False,
    'EMAIL_TEMPLATE': 'emails/job_expired.html',
}

# Cleanup configuration
CLEANUP_CONFIG = {
    # Delete failed job records after this many days
    'DELETE_FAILED_JOBS_AFTER': 30,
    
    # Delete completed job records after this many days
    'DELETE_COMPLETED_JOBS_AFTER': 90,
    
    # Keep cancelled job records for this many days
    'KEEP_CANCELLED_JOBS_FOR': 14,
    
    # Archive old logs after this many days
    'ARCHIVE_LOGS_AFTER': 60,
}
