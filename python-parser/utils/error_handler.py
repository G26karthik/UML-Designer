"""
Standardized Error Handling for Python Parser Service
Provides consistent error responses and logging
"""

import logging
import traceback
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from flask import jsonify

class ErrorType(Enum):
    """Standard error types for categorization"""
    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    INTERNAL = "INTERNAL"
    SECURITY = "SECURITY"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"

class ErrorCode:
    """HTTP status codes for different error types"""
    ERROR_CODES = {
        ErrorType.VALIDATION: 400,
        ErrorType.NOT_FOUND: 404,
        ErrorType.TIMEOUT: 408,
        ErrorType.PAYLOAD_TOO_LARGE: 413,
        ErrorType.EXTERNAL_SERVICE: 502,
        ErrorType.INTERNAL: 500,
        ErrorType.SECURITY: 403,
        ErrorType.RESOURCE_LIMIT: 413
    }
    
    @classmethod
    def get_code(cls, error_type: ErrorType) -> int:
        return cls.ERROR_CODES.get(error_type, 500)

class AppError(Exception):
    """Application-specific error with standardized structure"""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.INTERNAL, 
                 details: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = ErrorCode.get_code(error_type)
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        self.is_operational = True  # Distinguishes from programming errors

def create_error_response(error: Exception, request_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
    """Creates standardized error response format"""
    
    if isinstance(error, AppError):
        app_error = error
    else:
        # Convert standard exceptions to AppError
        if isinstance(error, (FileNotFoundError, OSError)):
            app_error = AppError("Resource not found", ErrorType.NOT_FOUND, cause=error)
        elif isinstance(error, (MemoryError,)):
            app_error = AppError("Insufficient memory", ErrorType.RESOURCE_LIMIT, cause=error)
        elif isinstance(error, (TimeoutError,)):
            app_error = AppError("Operation timed out", ErrorType.TIMEOUT, cause=error)
        elif isinstance(error, (ValueError, TypeError)):
            app_error = AppError("Invalid input data", ErrorType.VALIDATION, cause=error)
        else:
            app_error = AppError("Internal server error", ErrorType.INTERNAL, cause=error)
    
    response = {
        "success": False,
        "error": {
            "message": app_error.message,
            "type": app_error.error_type.value,
            "timestamp": app_error.timestamp
        }
    }
    
    # Add details if available and not in production
    if app_error.details and not _is_production():
        response["error"]["details"] = app_error.details
        
    if request_id:
        response["error"]["requestId"] = request_id
    
    # Don't expose internal details in production
    if _is_production() and app_error.error_type == ErrorType.INTERNAL:
        response["error"]["message"] = "Internal server error"
    
    return response, app_error.status_code

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Logs errors with consistent format and appropriate level"""
    
    if isinstance(error, AppError):
        log_level = logging.ERROR if error.status_code >= 500 else logging.WARNING
        
        log_data = {
            "error_type": error.error_type.value,
            "status_code": error.status_code,
            "message": error.message,
            "timestamp": error.timestamp
        }
        
        if error.details:
            log_data["details"] = error.details
            
        if error.cause:
            log_data["cause"] = str(error.cause)
            
        if context:
            log_data["context"] = context
            
        logging.log(log_level, f"Application Error: {error.message}", extra=log_data)
        
        # Log stack trace for internal errors
        if error.error_type == ErrorType.INTERNAL:
            logging.error(f"Stack trace: {traceback.format_exc()}")
    else:
        logging.error(f"Unhandled exception: {str(error)}", exc_info=True)

def handle_error(func):
    """Decorator to handle errors in Flask route handlers"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(e, {"function": func.__name__})
            response, status_code = create_error_response(e)
            return jsonify(response), status_code
    
    wrapper.__name__ = func.__name__
    return wrapper

def _is_production() -> bool:
    """Check if running in production environment"""
    import os
    return os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production'

# Common error creators for frequent scenarios
def create_validation_error(message: str, field: Optional[str] = None) -> AppError:
    """Create validation error with optional field information"""
    details = {"field": field} if field else None
    return AppError(message, ErrorType.VALIDATION, details)

def create_security_error(message: str, threat_type: Optional[str] = None) -> AppError:
    """Create security-related error"""
    details = {"threat_type": threat_type} if threat_type else None
    return AppError(message, ErrorType.SECURITY, details)

def create_timeout_error(operation: str, timeout_seconds: Optional[int] = None) -> AppError:
    """Create timeout error with operation context"""
    details = {"timeout_seconds": timeout_seconds} if timeout_seconds else None
    return AppError(f"{operation} timed out", ErrorType.TIMEOUT, details)

def create_resource_limit_error(resource: str, limit: Optional[str] = None) -> AppError:
    """Create resource limit error"""
    details = {"limit": limit} if limit else None
    return AppError(f"{resource} limit exceeded", ErrorType.RESOURCE_LIMIT, details)

def create_external_service_error(service: str, cause: Optional[Exception] = None) -> AppError:
    """Create external service error"""
    return AppError(f"{service} service unavailable", ErrorType.EXTERNAL_SERVICE, cause=cause)