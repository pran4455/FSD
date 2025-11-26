import os
import sys
import logging
from datetime import datetime

def setup_auth_logger():
    
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    logger = logging.getLogger('auth_events')
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    log_file = os.path.join(logs_dir, 'auth_events.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    file_handler.flush()
    
    return logger

def get_auth_logger():
    
    logger = logging.getLogger('auth_events')
    if not logger.handlers:
        return setup_auth_logger()
    return logger

def sanitize_log_field(value):
    
    if value is None:
        return ''
    
    value_str = str(value)
    value_str = value_str.replace('|', '_')
    value_str = value_str.replace('\n', ' ').replace('\r', ' ')
    value_str = ''.join(char if ord(char) >= 32 or char == '\t' else ' ' for char in value_str)
    
    return value_str.strip()

def log_login_attempt(username, success, auth_method, reason=None):
    
    try:
        logger = get_auth_logger()
        
        username = sanitize_log_field(username)
        auth_method = sanitize_log_field(auth_method)
        reason = sanitize_log_field(reason) if reason else ''
        
        status = 'SUCCESS' if success else 'FAILED'
        level = logging.INFO if success else logging.WARNING
        
        message = f"LOGIN | username={username} | status={status} | method={auth_method}"
        if reason:
            message += f" | reason={reason}"
        
        logger.log(level, message)
        
        for handler in logger.handlers:
            handler.flush()
            
    except Exception as e:
        print(f"Logging error: {e}", file=sys.stderr)

def log_totp_verification(username, success):
    
    try:
        logger = get_auth_logger()
        
        username = sanitize_log_field(username)
        
        status = 'SUCCESS' if success else 'FAILED'
        level = logging.INFO if success else logging.WARNING
        
        message = f"TOTP_VERIFY | username={username} | status={status}"
        
        logger.log(level, message)
        
        for handler in logger.handlers:
            handler.flush()
            
    except Exception as e:
        print(f"Logging error: {e}", file=sys.stderr)

def log_logout(username, session_duration=None):
    
    try:
        logger = get_auth_logger()
        
        username = sanitize_log_field(username)
        
        message = f"LOGOUT | username={username} | status=SUCCESS"
        if session_duration is not None:
            message += f" | duration={session_duration:.1f}"
        
        logger.info(message)
        
        for handler in logger.handlers:
            handler.flush()
            
    except Exception as e:
        print(f"Logging error: {e}", file=sys.stderr)
