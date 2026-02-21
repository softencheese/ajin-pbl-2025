# !/usr/bin/env python3
# """DB 클리어 스크립트
# 
# 사용법 예시:
#   python clear.db.py            # 모든 테이블의 행 수를 보여주고 확인 후 삭제
#   python clear.db.py -y        # 확인 건너뛰고 바로 삭제
#   python clear.db.py --truncate -y   # TRUNCATE 시도 (MySQL에서 더 빠름)
#   python clear.db.py --tables rfid_reader_location,lot -y  # 특정 테이블만 삭제
# 
# 주의: 프로덕션 DB에서 사용하지 마세요. 백업 후 사용하세요.
# """

import os
import sys
import argparse
from typing import List

# Make project package importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, text
from app.core.database import SessionLocal, engine, Base
# Import models so that their tables are registered on Base.metadata
from app.models.process import Process
from app.models.item import Item
from app.models.rfid import RFIDReaderLocation
from app.models.lot import Lot
from app.models.pallet import Pallet


def get_table_counts(conn):
	"""Return dict of table_name -> row count using the given connection."""
	counts = {}
	for table in Base.metadata.sorted_tables:
		try:
			res = conn.execute(select(func.count()).select_from(table))
			counts[table.name] = int(res.scalar_one())
		except Exception:
			counts[table.name] = None
	return counts


def _find_table_by_name(name: str):
	return next((t for t in Base.metadata.sorted_tables if t.name == name), None)


def clear_tables(conn, table_names: List[str] = None, use_truncate: bool = False):
	"""Delete all rows from tables. If table_names is None, clear all tables.

	Deletion happens in reverse dependency order to respect foreign keys.
	"""
	tables = list(Base.metadata.sorted_tables)
	if table_names:
		tables = [t for t in tables if t.name in table_names]
	# reverse to delete children before parents
	tables = list(reversed(tables))

	if use_truncate:
		# Try to disable FK checks for databases that support it (MySQL)
		try:
			conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
		except Exception:
			pass

	for table in tables:
		try:
			if use_truncate:
				conn.execute(text(f"TRUNCATE TABLE {table.name}"))
			else:
				conn.execute(table.delete())
			print(f"Cleared: {table.name}")
		except Exception as e:
			print(f"Failed to clear {table.name}: {e}")

	if use_truncate:
		try:
			conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
		except Exception:
			pass


def main():
	parser = argparse.ArgumentParser(description="Clear DB rows (safe preview + confirmation)")
	parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation and proceed")
	parser.add_argument("--truncate", action="store_true", help="Try TRUNCATE TABLE (may require DB-specific privileges)")
	parser.add_argument("--tables", type=str, help="Comma-separated table names to clear (default: all)")
	args = parser.parse_args()

	specified_tables = None
	if args.tables:
		specified_tables = [t.strip() for t in args.tables.split(",") if t.strip()]

	# Show counts
	with engine.connect() as conn:
		counts = get_table_counts(conn)

	print("Current row counts:")
	for name, cnt in counts.items():
		print(f" - {name}: {cnt if cnt is not None else 'unknown'}")

	if specified_tables:
		print(f"Will clear only: {', '.join(specified_tables)}")
	else:
		print("Will clear all tables registered in metadata.")

	# Perform deletion inside a transaction
	with engine.begin() as conn:
		table_names = specified_tables if specified_tables else None
		if table_names:
			# validate table names
			invalid = [t for t in table_names if _find_table_by_name(t) is None]
			if invalid:
				print(f"Invalid table names: {', '.join(invalid)}")
				return
		clear_tables(conn, table_names, use_truncate=args.truncate)

	print("Done.")


if __name__ == '__main__':
	main()


