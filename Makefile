# Makefile for RFID Logistics Tracking System

.PHONY: help up down clean fclean test seed

# ============================================
# 도움말
# ============================================
help:
	@echo "사용 가능한 명령어:"
	@echo ""
	@echo "  기본 명령어:"
	@echo "    make up          - 모든 서비스 시작 (DB, API, Frontend)"
	@echo "    make down        - 모든 서비스 종료"
	@echo "    make logs        - 서비스 로그 확인"
	@echo ""
	@echo "  정리:"
	@echo "    make clean       - 임시 파일 제거 (__pycache__ 등)"
	@echo "    make fclean      - 완전 초기화 (DB 데이터, 환경 모두 삭제)"
	@echo ""
	@echo "  테스트:"
	@echo "    make test        - pytest 실행"
	@echo "    make seed        - 테스트용 가상 데이터 삽입"
	@echo "    make virt-reader - 가상 RFID 리더기 실행"

# ============================================
# 서비스 시작/종료
# ============================================
up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# ============================================
# 정리
# ============================================
clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Clean complete."

fclean: clean
	@echo "Performing deep clean (removing data and environments)..."
	@docker-compose down -v 2>/dev/null || true
	@rm -rf implementation/data
	@rm -rf implementation/api/venv
	@rm -rf implementation/frontend/node_modules
	@rm -rf implementation/api/logs
	@rm -rf implementation/backups
	@echo "Deep clean complete. System is factory reset."

# ============================================
# 테스트
# ============================================
test:
	@echo "Running pytest..."
	docker exec ajin_rfid_api pytest tests/ -v

seed:
	@echo "Inserting test data..."
	docker exec ajin_rfid_api python scripts/init_db.py
	@echo "Test data seeding complete."

virt-reader:
	@cd ./implementation/virt_reader && make