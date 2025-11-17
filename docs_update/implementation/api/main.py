"""
AJIN RFID 물류 추적 시스템 - FastAPI 서버
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# FastAPI 앱 생성
app = FastAPI(
    title="AJIN RFID 물류 추적 시스템",
    description="RFID 기반 팔레트 추적 및 물류 관리 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/")
async def root():
    return {
        "service": "AJIN RFID 물류 추적 시스템",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"  # TODO: 실제 DB 연결 확인
    }

# TODO: 라우터 추가
# from app.routes import rfid, pallets, lots, materials, parts, processes
# app.include_router(rfid.router, prefix="/api/v1/rfid", tags=["RFID"])
# app.include_router(pallets.router, prefix="/api/v1/pallets", tags=["Pallets"])
# ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
