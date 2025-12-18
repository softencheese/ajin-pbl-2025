
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 요청 정보 (필요시 body도 로깅 가능하나, 보안/성능상 주의)
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = request.url.path
        
        # 처리
        try:
            response = await call_next(request)
            
            # 처리 시간 계산
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            status_code = response.status_code
            
            # 로그 메시지 작성
            log_message = f"{method} {url} - Status: {status_code} - IP: {client_ip} - Time: {process_time_ms}ms"
            
            if status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)
                
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            process_time_ms = round(process_time * 1000, 2)
            
            logger.error(f"{method} {url} - Failed - IP: {client_ip} - Time: {process_time_ms}ms - Error: {str(e)}", exc_info=True)
            raise e
