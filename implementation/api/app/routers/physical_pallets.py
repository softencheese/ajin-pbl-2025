"""실물 팔레트 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.core.database import get_db
from app.core.permissions import PermissionChecker
from app.models.user import User
from app.models.physical_pallet import PhysicalPallet
from app.models.item import Item
from app.models.process import Process
from app.schemas.physical_pallet import (
    PhysicalPalletCreate,
    PhysicalPalletUpdate,
    PhysicalPalletResponse,
    PhysicalPalletListResponse,
    PhysicalPalletStatusUpdate
)
import math

router = APIRouter()


def _build_physical_pallet_response(pallet: PhysicalPallet, db: Session) -> dict:
    """실물 팔레트 응답 데이터 구성"""
    response_data = {
        "id": pallet.id,
        "epc": pallet.epc,
        "pallet_code": pallet.pallet_code,
        "item_id": pallet.item_id,
        "status": pallet.status.value if hasattr(pallet.status, 'value') else pallet.status,
        "description": pallet.description,
        "created_at": pallet.created_at,
        "updated_at": getattr(pallet, 'updated_at', None),
    }

    # 연관 품목 정보
    if pallet.item_id:
        item = db.query(Item).filter(Item.id == pallet.item_id).first()
        if item:
            response_data["item_code"] = item.item_code
            response_data["item_name"] = item.item_name

    return response_data


@router.post("", response_model=PhysicalPalletResponse, status_code=201)
async def create_physical_pallet(
    data: PhysicalPalletCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "write"))
):
    """실물 팔레트 생성 (권한: physical_pallets:write)"""
    
    # EPC 중복 체크
    existing_epc = db.query(PhysicalPallet).filter(PhysicalPallet.epc == data.epc).first()
    if existing_epc:
        raise HTTPException(status_code=400, detail=f"이미 존재하는 EPC입니다: {data.epc}")
    
    # 팔레트 코드 중복 체크
    existing_code = db.query(PhysicalPallet).filter(PhysicalPallet.pallet_code == data.pallet_code).first()
    if existing_code:
        raise HTTPException(status_code=400, detail=f"이미 존재하는 팔레트 코드입니다: {data.pallet_code}")
    
    # 품목 존재 확인
    if data.item_id:
        item = db.query(Item).filter(Item.id == data.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"품목을 찾을 수 없습니다: {data.item_id}")
    
    # 실물 팔레트 생성
    physical_pallet = PhysicalPallet(
        epc=data.epc,
        pallet_code=data.pallet_code,
        item_id=data.item_id,
        status=data.status,
        description=data.description
    )
    
    db.add(physical_pallet)
    db.commit()
    db.refresh(physical_pallet)
    
    return _build_physical_pallet_response(physical_pallet, db)


@router.get("", response_model=PhysicalPalletListResponse)
async def list_physical_pallets(
    page: int = Query(1, ge=1, description="페이지 번호"),
    per_page: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    status: Optional[str] = Query(None, description="상태 필터"),
    item_id: Optional[int] = Query(None, description="품목 ID 필터"),
    search: Optional[str] = Query(None, description="검색어 (EPC, 팔레트 코드)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "read"))
):
    """실물 팔레트 목록 조회 (권한: physical_pallets:read)"""
    
    query = db.query(PhysicalPallet)
    
    # 필터 적용
    if status:
        query = query.filter(PhysicalPallet.status == status)
    
    if item_id:
        query = query.filter(PhysicalPallet.item_id == item_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (PhysicalPallet.epc.like(search_pattern)) |
            (PhysicalPallet.pallet_code.like(search_pattern))
        )
    
    # 전체 개수 조회
    total = query.count()
    
    # 페이징 적용
    offset = (page - 1) * per_page
    pallets = query.order_by(PhysicalPallet.created_at.desc()).offset(offset).limit(per_page).all()
    
    # 응답 구성
    items = [_build_physical_pallet_response(p, db) for p in pallets]
    pages = math.ceil(total / per_page) if total > 0 else 0
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages
    }


@router.get("/{pallet_id}", response_model=PhysicalPalletResponse)
async def get_physical_pallet(
    pallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "read"))
):
    """실물 팔레트 상세 조회 (권한: physical_pallets:read)"""
    
    pallet = db.query(PhysicalPallet).filter(PhysicalPallet.id == pallet_id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail=f"실물 팔레트를 찾을 수 없습니다: {pallet_id}")
    
    return _build_physical_pallet_response(pallet, db)


@router.get("/epc/{epc}", response_model=PhysicalPalletResponse)
async def get_physical_pallet_by_epc(
    epc: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "read"))
):
    """EPC로 실물 팔레트 조회 (권한: physical_pallets:read)"""
    
    pallet = db.query(PhysicalPallet).filter(PhysicalPallet.epc == epc).first()
    if not pallet:
        raise HTTPException(status_code=404, detail=f"실물 팔레트를 찾을 수 없습니다: {epc}")
    
    return _build_physical_pallet_response(pallet, db)


@router.get("/code/{pallet_code}", response_model=PhysicalPalletResponse)
async def get_physical_pallet_by_code(
    pallet_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "read"))
):
    """팔레트 코드로 실물 팔레트 조회 (권한: physical_pallets:read)"""
    
    pallet = db.query(PhysicalPallet).filter(PhysicalPallet.pallet_code == pallet_code).first()
    if not pallet:
        raise HTTPException(status_code=404, detail=f"실물 팔레트를 찾을 수 없습니다: {pallet_code}")
    
    return _build_physical_pallet_response(pallet, db)


@router.patch("/{pallet_id}", response_model=PhysicalPalletResponse)
async def update_physical_pallet(
    pallet_id: int,
    data: PhysicalPalletUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "write"))
):
    """실물 팔레트 수정 (권한: physical_pallets:write)"""
    
    pallet = db.query(PhysicalPallet).filter(PhysicalPallet.id == pallet_id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail=f"실물 팔레트를 찾을 수 없습니다: {pallet_id}")
    
    # 팔레트 코드 중복 체크
    if data.pallet_code and data.pallet_code != pallet.pallet_code:
        existing = db.query(PhysicalPallet).filter(
            PhysicalPallet.pallet_code == data.pallet_code,
            PhysicalPallet.id != pallet_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"이미 존재하는 팔레트 코드입니다: {data.pallet_code}")
    
    # 품목 존재 확인
    if data.item_id:
        item = db.query(Item).filter(Item.id == data.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"품목을 찾을 수 없습니다: {data.item_id}")
    
    # 데이터 업데이트
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pallet, key, value)
    
    db.commit()
    db.refresh(pallet)
    
    return _build_physical_pallet_response(pallet, db)


@router.patch("/{pallet_id}/status", response_model=PhysicalPalletResponse)
async def update_physical_pallet_status(
    pallet_id: int,
    data: PhysicalPalletStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "write"))
):
    """실물 팔레트 상태 변경 (권한: physical_pallets:write)"""
    
    pallet = db.query(PhysicalPallet).filter(PhysicalPallet.id == pallet_id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail=f"실물 팔레트를 찾을 수 없습니다: {pallet_id}")
    
    pallet.status = data.status
    db.commit()
    db.refresh(pallet)
    
    return _build_physical_pallet_response(pallet, db)


@router.delete("/{pallet_id}", status_code=204)
async def delete_physical_pallet(
    pallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "delete"))
):
    """실물 팔레트 삭제 (권한: physical_pallets:delete)"""
    
    pallet = db.query(PhysicalPallet).filter(PhysicalPallet.id == pallet_id).first()
    if not pallet:
        raise HTTPException(status_code=404, detail=f"실물 팔레트를 찾을 수 없습니다: {pallet_id}")
    
    db.delete(pallet)
    db.commit()
    
    return None


@router.get("/statistics/summary")
async def get_physical_pallet_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionChecker("physical_pallets", "read"))
):
    """실물 팔레트 통계 조회 (권한: physical_pallets:read)"""
    
    # 전체 팔레트 수
    total_count = db.query(func.count(PhysicalPallet.id)).scalar()
    
    # 상태별 통계
    status_stats = db.query(
        PhysicalPallet.status,
        func.count(PhysicalPallet.id).label("count")
    ).group_by(PhysicalPallet.status).all()
    
    status_breakdown = {stat.status: stat.count for stat in status_stats}
    
    return {
        "total_count": total_count,
        "status_breakdown": status_breakdown,
        "generated_pallets": status_breakdown.get("Generated", 0),
        "empty_pallets": status_breakdown.get("Empty", 0),
        "stock_pallets": status_breakdown.get("Stock", 0),
        "consuming_pallets": status_breakdown.get("Consuming", 0),
        "producing_pallets": status_breakdown.get("Producing", 0),
        "finished_pallets": status_breakdown.get("Finished", 0),
        "deregistered_pallets": status_breakdown.get("Deregistered", 0),
        "hold_pallets": status_breakdown.get("Hold", 0),
        "defect_pallets": status_breakdown.get("Defect", 0)
    }
