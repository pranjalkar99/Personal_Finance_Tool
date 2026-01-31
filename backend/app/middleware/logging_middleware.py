"""Request/Response logging middleware."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import get_logger

logger = get_logger("middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Get request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"[{request_id}] {method} {path} - Started",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "client_ip": client_ip
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log response
            log_method = logger.info if response.status_code < 400 else logger.warning
            log_method(
                f"[{request_id}] {method} {path} - {response.status_code} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"[{request_id}] {method} {path} - Error: {str(e)} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms
                },
                exc_info=True
            )
            raise

