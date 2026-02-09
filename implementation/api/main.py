"""
AJIN RFID 물류 추적 시스템 - FastAPI 서버
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.core.socket import sio_app # Socket.IO 앱 임포트
from app.core.logging import setup_logging
from app.middlewares.logging import LoggingMiddleware
from app.routers import (
    rfid_router,
    auth_router,
    users_router, 
    pallets_router,
    physical_pallets_router,
    trace_router,
    items_router,
    processes_router,
    reader_locations_router,
    lots_router,
    lot_genealogy_router,
    # rfid_tags_router 삭제됨 - pallets로 통합
    # rfid_tags_router 삭제됨 - pallets로 통합
    dashboard_router
)
from app.core.config import settings

from contextlib import asynccontextmanager

# 데이터베이스 테이블 생성 (개발용)
# 프로덕션에서는 Alembic 마이그레이션을 사용하는 것이 좋습니다.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 로깅 설정 초기화
    setup_logging()
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="AJIN RFID Tracking API",
    description="RFID 기반 물류 추적 시스템 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
origins = settings.CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 미들웨어 추가 (CORS 뒤에 위치하여 모든 요청 기록)
app.add_middleware(LoggingMiddleware)

# Socket.IO 앱 마운트
app.mount("/socket.io", sio_app)

# 라우터 등록
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["User Management"])
app.include_router(rfid_router, prefix="/api/v1/rfid", tags=["RFID"])
app.include_router(pallets_router, prefix="/api/v1/pallets", tags=["Pallets"])
app.include_router(physical_pallets_router, prefix="/api/v1/physical-pallets", tags=["Physical Pallets"])
app.include_router(trace_router, prefix="/api/v1/trace", tags=["Traceability"])
app.include_router(items_router, prefix="/api/v1/items", tags=["Items"])
app.include_router(processes_router, prefix="/api/v1/processes", tags=["Processes"])
app.include_router(reader_locations_router, prefix="/api/v1/reader-locations", tags=["Reader Locations"])
app.include_router(lots_router, prefix="/api/v1/lots", tags=["Lots"])
app.include_router(lot_genealogy_router, prefix="/api/v1/lot-genealogy", tags=["Lot Genealogy"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {"message": "AJIN RFID Tracking API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
