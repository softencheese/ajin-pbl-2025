"""모니터링 및 대시보드 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional, List
from datetime import date, datetime, timedelta
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.pallet import Pallet, PalletHistory
from app.models.physical_pallet import PhysicalPallet
from app.models.lot import Lot
from app.models.item import Item
from app.models.process import Process
from app.models.rfid import RFIDReaderLocation
from app.schemas.dashboard import (
    DashboardSummary,
    ProcessStatus,
    ProcessStatusList,
    ReaderStatus,
    ReaderStatusList,
    StockItem,
    StockInventoryResponse,
    LotStock
)

from app.core.permissions import PermissionChecker
from app.models.user import User

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("dashboard", "read"))
):
    """
    대시보드 요약 정보 (권한: dashboard:read)
    
    - 활성 팔레트 수
    - 총 재고 수량
    - 금일 생산량
    - 리더기 연결 상태
    """
    # 활성 팔레트 수 (Deregistered, Defect 제외)
    active_pallets = db.query(func.count(Pallet.id)).join(
        PhysicalPallet, Pallet.physical_pallet_id == PhysicalPallet.id, isouter=True
    ).filter(
        PhysicalPallet.status.notin_(["Deregistered", "Defect", "Generated"])
    ).scalar()
    
    # 총 재고 수량 (Stock 상태 팔레트의 수량 합계)
    # Lot의 quantity를 사용 (pallet에는 quantity 필드 없음)
    total_stock = db.query(func.sum(Lot.quantity)).join(
        Pallet, Lot.id == Pallet.lot_id
    ).join(
        PhysicalPallet, Pallet.physical_pallet_id == PhysicalPallet.id, isouter=True
    ).filter(
        PhysicalPallet.status == "Stock"
    ).scalar() or 0
    
    # 금일 생산량 (오늘 생산된 LOT 수량 합계)
    today = date.today()
    today_production = db.query(func.sum(Lot.quantity)).filter(
        Lot.production_date == today
    ).scalar() or 0
    
    # 리더기 상태 (총 수 vs 활성 수)
    total_readers = db.query(func.count(RFIDReaderLocation.id)).scalar()
    connected_readers = db.query(func.count(RFIDReaderLocation.id)).filter(
        RFIDReaderLocation.is_active == True
    ).scalar()
    
    return DashboardSummary(
        active_pallets=active_pallets,
        total_stock=total_stock,
        today_production=today_production,
        reader_status={
            "connected": connected_readers,
            "total": total_readers
        }
    )


@router.get("/process-status", response_model=ProcessStatusList)
async def get_process_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("dashboard", "read"))
):
    """
    공정별 현황 (권한: dashboard:read)
    
    각 공정의 활성 팔레트 수와 상태별 분포를 반환합니다.
    (N+1 쿼리 최적화: 단일 쿼리로 집계)
    """
    # 단일 쿼리로 모든 공정의 팔레트 상태별 집계
    # physical_pallet의 status를 사용
    status_data = db.query(
        Pallet.current_process_id,
        PhysicalPallet.status,
        func.count(Pallet.id)
    ).join(
        PhysicalPallet, Pallet.physical_pallet_id == PhysicalPallet.id, isouter=True
    ).filter(
        Pallet.current_process_id.isnot(None),
        PhysicalPallet.status.notin_(["Deregistered", "Defect", "Generated"])
    ).group_by(Pallet.current_process_id, PhysicalPallet.status).all()
    
    # 공정별로 데이터 정리
    process_map = {}
    for process_id, status, count in status_data:
        if process_id not in process_map:
            process_map[process_id] = {}
        process_map[process_id][status] = count
    
    # 공정 목록 조회
    processes = db.query(Process).order_by(Process.process_order).all()
    
    process_statuses = []
    total_active = 0
    
    for process in processes:
        status_breakdown = process_map.get(process.id, {})
        active_count = sum(status_breakdown.values())
        total_active += active_count
        
        process_statuses.append(ProcessStatus(
            process_id=process.id,
            process_name=process.process_name,
            production_line=process.production_line,
            active_pallets=active_count,
            status_breakdown=status_breakdown
        ))
    
    return ProcessStatusList(
        processes=process_statuses,
        total_active_pallets=total_active,
        last_updated=datetime.now()
    )


@router.get("/readers", response_model=ReaderStatusList)
async def get_reader_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("dashboard", "read"))
):
    """
    리더기 상태 조회 (권한: dashboard:read)
    
    모든 등록된 리더기의 연결 상태와 마지막 스캔 시간을 반환합니다.
    last_scan_time은 rfid_reader_locations 테이블에 직접 저장되어 조인 없이 빠르게 조회됩니다.
    """
    locations = db.query(RFIDReaderLocation).all()
    
    readers = []
    for loc in locations:
        readers.append(ReaderStatus(
            id=loc.id,
            port_name=loc.port_name,
            process_name=loc.process.process_name if loc.process else None,
            location_type=loc.location_type,
            status="CONNECTED" if loc.is_active else "DISCONNECTED",
            last_scan_time=loc.last_scan_time,  # 컬럼에서 바로 조회 (조인 없음)
            is_active=loc.is_active
        ))
    
    return ReaderStatusList(readers=readers)


@router.get("/inventory/stock", response_model=StockInventoryResponse)
async def get_stock_inventory(
    item_code: Optional[str] = Query(None, alias="part_number"), # 호환성 유지 위해 alias 사용
    process_id: Optional[int] = None,
    sort: str = Query("production_date", description="정렬 기준"),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("dashboard", "read"))
):
    """
    재고 현황 (FIFO 관리용) (권한: dashboard:read)
    
    품번/공정별 재고를 생산일자순으로 정렬하여 반환합니다.
    경과일에 따른 긴급도 표시 포함.
    """
    # Stock 상태 팔레트 조회
    # physical_pallet의 status를 사용
    query = db.query(Pallet).join(
        PhysicalPallet, Pallet.physical_pallet_id == PhysicalPallet.id, isouter=True
    ).filter(PhysicalPallet.status == "Stock")
    
    # LOT와 조인
    query = query.join(Lot, Pallet.lot_id == Lot.id, isouter=True)
    
    if process_id:
        query = query.filter(Pallet.current_process_id == process_id)
    
    pallets = query.all()
    
    # 품번별로 그룹화
    stock_by_item = {}
    
    for pallet in pallets:
        if not pallet.lot:
            continue
        
        # Lot -> Item
        item = pallet.lot.item
        if not item:
            continue

        if item_code and item.item_code != item_code:
            continue
        
        key = (item.item_code, pallet.current_process_id)
        
        if key not in stock_by_item:
            process_name = pallet.current_process.process_name if pallet.current_process else None
            stock_by_item[key] = {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "vehicle_model": item.vehicle_model,
                "process_name": process_name,
                "production_line": pallet.current_process.production_line if pallet.current_process else None,
                "lots": []
            }
        
        # 경과일 계산
        days_old = (date.today() - pallet.lot.production_date).days
        
        # 긴급도 판정
        if days_old >= 5:
            urgency = "urgent"
        elif days_old >= 3:
            urgency = "warning"
        else:
            urgency = "normal"
        
        # quantity는 lot.quantity 사용, 없으면 item.pallet_capacity, 그것도 없으면 0
        quantity = pallet.lot.quantity if pallet.lot.quantity else (
            item.pallet_capacity if item.pallet_capacity else 0
        )
        
        stock_by_item[key]["lots"].append({
            "lot_no": pallet.lot.lot_number,
            "pallet_no": pallet.pallet_no,
            "production_date": pallet.lot.production_date,
            "days_old": days_old,
            "quantity": quantity,
            "status": urgency
        })
    
    # 각 품번의 LOT를 생산일자순 정렬
    stock_items = []
    for key, data in stock_by_item.items():
        data["lots"].sort(key=lambda x: x["production_date"])
        # LotStock 모델로 변환
        data["lots"] = [LotStock(**lot) for lot in data["lots"]]
        stock_items.append(StockItem(**data))
    
    return StockInventoryResponse(stock_items=stock_items)


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("dashboard", "read"))
):
    """
    최근 활동 이력 (권한: dashboard:read)
    
    최근 팔레트 상태 변경 이력을 반환합니다.
    """
    histories = db.query(PalletHistory).order_by(
        PalletHistory.scan_time.desc()
    ).limit(limit).all()
    
    activities = []
    for h in histories:
        pallet = db.query(Pallet).filter(Pallet.id == h.pallet_id).first()
        process = db.query(Process).filter(Process.id == h.process_id).first() if h.process_id else None
        
        activities.append({
            "id": h.id,
            "pallet_no": pallet.pallet_no if pallet else None,
            "event_type": h.event_type,
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "process_name": process.process_name if process else None,
            "scan_time": h.scan_time,
            "worker_name": h.worker_name,
            "notes": h.notes
        })
    
    return {"activities": activities, "total": len(activities)}
