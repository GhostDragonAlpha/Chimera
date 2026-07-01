"""
Rate Limit Validation Utilities for API Configuration.
Validates configured request rates, batch sizes, and concurrent limits against typical API rate limit constraints.
"""

import logging

logger = logging.getLogger("Chimera")


def validate_request_rate(rpm: int = None, rps: float = None, max_rpm: int = 60, max_rps: float = 1.0) -> bool:
    """Validate that configured request rates comply with typical API rate limit constraints.
    
    Args:
        rpm: Requests per minute configured value.
        rps: Requests per second configured value.
        max_rpm: Maximum allowed requests per minute (default 60).
        max_rps: Maximum allowed requests per second (default 1.0).
        
    Returns:
        bool: True if valid, raises ValueError otherwise.
    """
    if rpm is not None and (not isinstance(rpm, int) or rpm <= 0):
        raise ValueError("rpm must be a positive integer")
    if rps is not None and (not isinstance(rps, (int, float)) or rps <= 0):
        raise ValueError("rps must be a positive number")
    
    calculated_rps = (float(rpm) / 60.0) if rpm is not None else (float(rps) if rps is not None else None)
    
    effective_max_rps = float(max_rpm) / 60.0 if max_rpm is not None else float(max_rps)
    
    if calculated_rps is not None:
        if rpm is not None and max_rpm is not None and rpm > max_rpm:
            raise ValueError(f"rpm {rpm} exceeds maximum allowed {max_rpm}")
        if rps is not None and max_rps is not None and rps > max_rps:
            raise ValueError(f"rps {rps} exceeds maximum allowed {max_rps}")
        if calculated_rps > effective_max_rps and rpm is not None and max_rpm is not None:
            logger.warning(f"Request rate {rpm} rpm ({calculated_rps} rps) exceeds typical API limits (max_rpm={max_rpm}, max_rps={max_rps})")
            
    return True


def validate_batch_size(batch_size: int, max_batch_size: int = 100) -> bool:
    """Validate that configured batch size complies with typical API batch size constraints.
    
    Args:
        batch_size: Configured batch size.
        max_batch_size: Maximum allowed batch size (default 100).
        
    Returns:
        bool: True if valid, raises ValueError otherwise.
    """
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if batch_size > max_batch_size:
        raise ValueError(f"batch_size {batch_size} exceeds maximum allowed {max_batch_size}")
    return True


def validate_concurrent_limits(concurrent_requests: int, max_concurrent: int = 10) -> bool:
    """Validate that configured concurrent limits comply with typical API concurrent request constraints.
    
    Args:
        concurrent_requests: Configured number of concurrent requests.
        max_concurrent: Maximum allowed concurrent requests (default 10).
        
    Returns:
        bool: True if valid, raises ValueError otherwise.
    """
    if not isinstance(concurrent_requests, int) or concurrent_requests <= 0:
        raise ValueError("concurrent_requests must be a positive integer")
    if concurrent_requests > max_concurrent:
        raise ValueError(f"concurrent_requests {concurrent_requests} exceeds maximum allowed {max_concurrent}")
    return True


def validate_api_rate_config(requests_per_minute: int = None, 
                             requests_per_second: float = None,
                             batch_size: int = None,
                             concurrent_limits: int = None,
                             max_rpm: int = 60,
                             max_rps: float = 1.0,
                             max_batch_size: int = 100,
                             max_concurrent: int = 10) -> dict:
    """Validate all API rate configuration parameters together."""
    errors = []
    
    try:
        validate_request_rate(requests_per_minute, requests_per_second, max_rpm, max_rps)
    except ValueError as e:
        errors.append(f"request_rate validation failed: {e}")
        
    if batch_size is not None:
        try:
            validate_batch_size(batch_size, max_batch_size)
        except ValueError as e:
            errors.append(f"batch_size validation failed: {e}")
            
    if concurrent_limits is not None:
        try:
            validate_concurrent_limits(concurrent_limits, max_concurrent)
        except ValueError as e:
            errors.append(f"concurrent_limits validation failed: {e}")
            
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
