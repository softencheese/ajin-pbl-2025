from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://ajin_user:ajin_password@localhost:3306/ajin_rfid?charset=utf8mb4"
    API_SECRET_KEY: str = "secret"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Authentication
    AUTH_ENABLED: bool = False  # 개발 편의를 위해 기본값 False (인증 우회)
    SECRET_KEY: str = "your-super-secret-key-change-it-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Default Permissions for new "USER" role
    # 모든 주요 리소스 읽기 + 현장 운영(Operational) 리소스 쓰기 권한 부여
    DEFAULT_USER_PERMISSIONS: dict = {
        # Master Data (Read Only)
        "items": ["read"],
        "processes": ["read"],
        "reader_locations": ["read"],
        
        # Operational Data (Read & Write)
        "pallets": ["read", "write"],
        "rfid": ["read", "write"], 
        "trace": ["read"], # Trace is typically read-only analysis
        "lots": ["read", "write"],
        "dashboard": ["read"]
    }

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
