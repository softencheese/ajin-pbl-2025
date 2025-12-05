from typing import Dict


class StateMachine:
    """팔레트 상태 전이 규칙 (pallet-state-machine.md 기반)"""
    
    # 유효한 상태 목록
    VALID_STATUSES = [
        "Generated",     # 생성됨 (등록만)
        "Empty",         # 빈 팔레트
        "Stock",         # 재고 (만차)
        "Consuming",     # 소비 중
        "Producing",     # 생산 중
        "Finished",      # 완제품
        "Deregistered",  # 등록 해제 (회수)
        "Hold",          # 보류
        "Defect"         # 불량
    ]
    
    def get_next_state(
        self, 
        current_status: str, 
        process_code: str, 
        location_type: str,
        is_final_product: bool = False
    ) -> Dict:
        """
        현재 상태, 공정, 위치를 기반으로 다음 상태를 결정합니다.
        
        Returns:
            {
                "allowed": bool,
                "next_status": str,
                "message": str
            }
        """
        
        # 1. 종료 상태 체크 (Deregistered, Defect는 전이 불가)
        if current_status in ["Deregistered", "Defect"]:
            return {
                "allowed": False,
                "next_status": current_status,
                "message": f"'{current_status}' 상태는 더 이상 전이할 수 없습니다."
            }
        
        # 2. Hold 상태 체크 (명시적 해제 필요)
        if current_status == "Hold" and location_type not in ["HOLD"]:
            return {
                "allowed": False,
                "next_status": current_status,
                "message": "Hold 상태는 관리자 권한으로 명시적 해제가 필요합니다."
            }
        
        # 3. 불량/보류 처리 우선
        if location_type == "DEFECT":
            return {
                "allowed": True,
                "next_status": "Defect",
                "message": "불량 처리되었습니다."
            }
        
        if location_type == "HOLD":
            if current_status == "Hold":
                # Hold 상태에서 다시 HOLD 리더기 태깅 시 해제 (원래 상태로 복귀 로직 필요)
                # 현재는 단순히 Stock으로 복귀
                return {
                    "allowed": True,
                    "next_status": "Stock",
                    "message": "보류 해제되었습니다."
                }
            return {
                "allowed": True,
                "next_status": "Hold",
                "message": "보류 처리되었습니다."
            }
        
        # 4. IN 리더기 (공정 투입)
        if location_type == "IN":
            if current_status == "Empty":
                # 빈 팔레트 투입 (적재용)
                return {
                    "allowed": True,
                    "next_status": "Producing",
                    "message": "생산 시작 (적재용 팔레트 투입)"
                }
            elif current_status == "Stock":
                # 만차 팔레트 투입 (소비용)
                return {
                    "allowed": True,
                    "next_status": "Consuming",
                    "message": "소비 시작 (투입 완료)"
                }
            else:
                return {
                    "allowed": False,
                    "next_status": current_status,
                    "message": f"IN 위치에서 '{current_status}' 상태는 처리할 수 없습니다."
                }
        
        # 5. OUT 리더기 (공정 완료)
        if location_type == "OUT":
            # 샤링 첫 공정 특수 처리
            if process_code == "SHEARING":
                if current_status == "Empty":
                    # 샤링에서 빈 팔레트 → 바로 생산 시작
                    return {
                        "allowed": True,
                        "next_status": "Producing",
                        "message": "샤링 생산 시작"
                    }
                elif current_status == "Producing":
                    # 샤링 생산 완료 → Stock
                    return {
                        "allowed": True,
                        "next_status": "Stock",
                        "message": "샤링 생산 완료 (재고 적재)"
                    }
            
            if current_status == "Producing":
                # 생산 완료
                if is_final_product:
                    return {
                        "allowed": True,
                        "next_status": "Finished",
                        "message": "완제품 생산 완료"
                    }
                else:
                    return {
                        "allowed": True,
                        "next_status": "Stock",
                        "message": "중간품 생산 완료 (재고 적재)"
                    }
            elif current_status == "Consuming":
                # 소비 완료 (빈 팔레트)
                return {
                    "allowed": True,
                    "next_status": "Empty",
                    "message": "소비 완료 (빈 팔레트)"
                }
            elif current_status == "Empty":
                # 빈 팔레트 OUT → 생산 시작
                return {
                    "allowed": True,
                    "next_status": "Producing",
                    "message": "생산 시작 (적재용 팔레트)"
                }
            else:
                return {
                    "allowed": False,
                    "next_status": current_status,
                    "message": f"OUT 위치에서 '{current_status}' 상태는 처리할 수 없습니다."
                }
        
        # 6. FINISH/RETURN 리더기 (완제품 출하/빈 팔레트 회수)
        if location_type in ["FINISH", "RETURN"]:
            if current_status == "Finished":
                return {
                    "allowed": True,
                    "next_status": "Deregistered",
                    "message": "완제품 출하 완료 (태그 회수)"
                }
            elif current_status == "Empty":
                return {
                    "allowed": True,
                    "next_status": "Deregistered",
                    "message": "빈 팔레트 회수 완료"
                }
            else:
                return {
                    "allowed": False,
                    "next_status": current_status,
                    "message": f"RETURN 위치에서 '{current_status}' 상태는 처리할 수 없습니다."
                }
        
        # 매칭되는 규칙이 없음
        return {
            "allowed": False,
            "next_status": current_status,
            "message": f"알 수 없는 위치 타입: {location_type}"
        }
