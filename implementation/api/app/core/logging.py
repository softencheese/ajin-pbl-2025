
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# 로그 디렉토리 및 하위 디렉토리 설정
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
SERVER_LOG_DIR = LOG_DIR / "server"
ERROR_LOG_DIR = LOG_DIR / "error"

for directory in [LOG_DIR, SERVER_LOG_DIR, ERROR_LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 로그 파일 경로
SERVER_LOG_FILE = SERVER_LOG_DIR / "server.log"
ERROR_LOG_FILE = ERROR_LOG_DIR / "error.log"

def setup_logging():
    """
    애플리케이션 로깅 설정
    """
    # 기본 포맷 설정 (JSON 형태나 구조화된 형태를 원하면 변경 가능)
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 루트 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 기존 핸들러 제거 (중복 방지)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. 콘솔 핸들러 (터미널 출력)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # 2. 파일 핸들러 (전체 로그, 날짜별 로테이션)
    # 매일 자정에 로그 파일 교체, 최대 30일 보관
    file_handler = TimedRotatingFileHandler(
        filename=SERVER_LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 3. 에러 파일 핸들러 (에러만 따로 저장)
    error_file_handler = TimedRotatingFileHandler(
        filename=ERROR_LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_file_handler.setFormatter(log_format)
    error_file_handler.setLevel(logging.ERROR)
    logger.addHandler(error_file_handler)

    # 서드파티 라이브러리 로그 레벨 조정 (너무 시끄러운 로그 방지)
    logging.getLogger("uvicorn.access").handlers = [] # uvicorn access 로그 중복 방지
    logging.getLogger("uvicorn.access").propagate = False # 직접 미들웨어로 찍을 예정
    
    return logger

# 전역에서 사용할 로거 객체 가져오기 함수
def get_logger(name: str):
    return logging.getLogger(name)
