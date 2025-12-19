#!/bin/bash

# 설정
# 스크립트 위치 기준으로 백업 디렉토리 설정 (implementation/backups)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")" # implementation/api/scripts -> implementation/api -> implementation
BACKUP_DIR="$PROJECT_ROOT/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
FILENAME="backup_${DATE}.sql"
CONTAINER_NAME="ajin_rfid_db"
MYSQL_USER="ajin_user"
MYSQL_PASSWORD="ajin_password"
MYSQL_DATABASE="ajin_rfid"

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# 백업 실행
echo "Backing up database to $BACKUP_DIR/$FILENAME..."
docker exec "$CONTAINER_NAME" mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" > "$BACKUP_DIR/$FILENAME"

if [ $? -eq 0 ]; then
  echo "Backup successful: $FILENAME"
else
  echo "Backup failed!"
  rm "$BACKUP_DIR/$FILENAME"
  exit 1
fi

# 30일 이상 된 오래된 백업 삭제
find "$BACKUP_DIR" -type f -name "*.sql" -mtime +30 -delete
echo "Old backups cleaned up."
