# AJIN RFID 시스템 시작 가이드

이 가이드는 개발 환경을 처음 설정하고 시스템을 실행하는 방법을 설명합니다.

## 사전 요구사항

### 1. 필수 소프트웨어 설치

#### Docker & Docker Compose
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose -y
sudo usermod -aG docker $USER
# 로그아웃 후 재로그인

# Docker 버전 확인
docker --version
docker-compose --version
```

#### Git
```bash
sudo apt-get install git -y
```

### 2. 저장소 클론

```bash
# 프로젝트 클론
git clone <repository-url>
cd Ajin_Pbl

# 브랜치 확인
git branch
```

## 초기 설정

### 1. 환경 변수 설정

```bash
# 예제 파일 복사
cp .env.example .env

# 환경 변수 파일 편집
nano .env  # 또는 vim, code 등
```

**중요**: 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!

```bash
# .env 파일 내용
MYSQL_ROOT_PASSWORD=your-secure-password-here
MYSQL_DATABASE=ajin_rfid
MYSQL_USER=ajin_user
MYSQL_PASSWORD=your-user-password-here
API_SECRET_KEY=generate-with-openssl-rand-hex-32
```

비밀 키 생성:
```bash
openssl rand -hex 32
```

### 2. 데이터 디렉토리 생성

```bash
# 호스트 볼륨 디렉토리 생성
mkdir -p data/mysql
mkdir -p data/backups
mkdir -p logs/api

# 권한 설정 (MySQL이 쓸 수 있도록)
sudo chown -R 999:999 data/mysql  # MySQL 컨테이너 UID
```

### 3. 데이터베이스 스키마 준비

```bash
# 기존 스키마 파일 복사
cp temp/DB/Ajin_DB.sql database/init/01-schema.sql

# 또는 직접 생성
nano database/init/01-schema.sql
```

## 시스템 실행

### 1. 전체 시스템 시작

```bash
# Docker Compose로 모든 서비스 시작
docker-compose up -d

# 실행 중인 컨테이너 확인
docker-compose ps
```

예상 출력:
```
NAME                IMAGE               STATUS
ajin-db             mysql:8.0           Up (healthy)
ajin-api            ajin_pbl-api        Up
ajin-frontend       ajin_pbl-frontend   Up
```

### 2. 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f frontend
```

### 3. 접속 확인

#### API 서버
브라우저에서 http://localhost:8000/docs 접속
- Swagger UI가 표시되어야 함
- `/health` 엔드포인트 테스트

#### 프론트엔드
브라우저에서 http://localhost:5173 접속
- React 애플리케이션이 로드되어야 함

#### 데이터베이스
```bash
# MySQL 클라이언트로 접속
docker exec -it ajin-db mysql -u root -p

# 또는 MySQL Workbench로 접속
# Host: localhost
# Port: 3306
# User: root
# Password: (your MYSQL_ROOT_PASSWORD)
```

## 개발 모드

Docker를 사용하지 않고 로컬에서 직접 실행하는 방법:

### API 서버 (FastAPI)

```bash
cd api

# 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화
source venv/bin/activate  # Linux/Mac
# Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export DATABASE_URL="mysql+pymysql://ajin_user:ajin_pass_2025@localhost:3306/ajin_rfid"
export API_SECRET_KEY="your-secret-key"

# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 (React)

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정 (.env.local 파일 생성)
echo "VITE_API_URL=http://localhost:8000" > .env.local

# 개발 서버 실행
npm run dev
```

## 일반적인 명령어

### Docker Compose

```bash
# 시작
docker-compose up -d

# 중지
docker-compose stop

# 재시작
docker-compose restart

# 특정 서비스 재시작
docker-compose restart api

# 중지 및 삭제
docker-compose down

# 볼륨까지 삭제 (주의: 데이터 손실!)
docker-compose down -v

# 로그 확인
docker-compose logs -f [service_name]

# 컨테이너 내부 접속
docker exec -it ajin-api /bin/bash
docker exec -it ajin-db /bin/bash
```

### 데이터베이스

```bash
# 백업 생성
docker exec ajin-db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ajin_rfid > ./data/backups/backup_$(date +%Y%m%d).sql

# 복구
docker exec -i ajin-db mysql -u root -p${MYSQL_ROOT_PASSWORD} ajin_rfid < ./data/backups/backup_20251117.sql

# 데이터베이스 재생성 (주의!)
docker exec -it ajin-db mysql -u root -p -e "DROP DATABASE IF EXISTS ajin_rfid; CREATE DATABASE ajin_rfid;"
docker exec -i ajin-db mysql -u root -p ajin_rfid < database/init/01-schema.sql
```

### Git

```bash
# 변경사항 확인
git status

# 변경사항 커밋
git add .
git commit -m "feat: 기능 추가"

# 푸시
git push origin main

# 풀
git pull origin main
```

## 트러블슈팅

### 1. 포트 충돌

에러: `port is already allocated`

**해결**:
```bash
# 사용 중인 프로세스 확인
sudo lsof -i :3306  # MySQL
sudo lsof -i :8000  # API
sudo lsof -i :5173  # Frontend

# 프로세스 종료
sudo kill -9 <PID>

# 또는 docker-compose.yml에서 포트 변경
ports:
  - "3307:3306"  # 호스트 포트 변경
```

### 2. MySQL 연결 실패

에러: `Can't connect to MySQL server`

**해결**:
```bash
# DB 헬스체크 확인
docker-compose ps

# DB 로그 확인
docker-compose logs db

# DB 컨테이너 재시작
docker-compose restart db

# DB 초기화 (주의: 데이터 손실)
docker-compose down
sudo rm -rf data/mysql/*
docker-compose up -d
```

### 3. 권한 오류

에러: `Permission denied`

**해결**:
```bash
# 데이터 디렉토리 권한 수정
sudo chown -R $USER:$USER data/
sudo chmod -R 755 data/

# MySQL 특정 권한
sudo chown -R 999:999 data/mysql
```

### 4. API 서버 500 에러

**해결**:
```bash
# API 로그 확인
docker-compose logs -f api

# DB 연결 확인
docker exec -it ajin-api /bin/bash
python -c "from app.database import engine; print(engine.connect())"

# 환경 변수 확인
docker exec -it ajin-api env | grep DATABASE_URL
```

### 5. 프론트엔드 빌드 실패

**해결**:
```bash
# node_modules 재설치
cd frontend
rm -rf node_modules
npm install

# 캐시 삭제
npm cache clean --force

# Docker 볼륨 재생성
docker-compose down
docker volume rm ajin_pbl_frontend_node_modules
docker-compose up -d frontend
```

## 다음 단계

1. **API 개발**: `api/app/routers/` 디렉토리에서 라우터 구현
2. **프론트엔드 개발**: `frontend/src/pages/` 디렉토리에서 페이지 구현
3. **임베디드 개발**: `embedded/src/` 디렉토리에서 C/C++ 코드 작성
4. **데이터베이스**: `database/migrations/` 디렉토리에서 스키마 변경 관리

## 참고 자료

- **구현 계획**: `.specify/plans/implementation-plan.md`
- **API 문서**: http://localhost:8000/docs
- **FastAPI 공식 문서**: https://fastapi.tiangolo.com/
- **React 공식 문서**: https://react.dev/
- **Docker Compose 문서**: https://docs.docker.com/compose/

## 도움이 필요하신가요?

- 프로젝트 구조: `README.md`
- 구현 상세: `.specify/plans/implementation-plan.md`
- 시스템 명세: `.specify/specs/rfid-logistics-tracking-system.md`
