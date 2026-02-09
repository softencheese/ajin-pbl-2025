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

    def next_status(self, allowed: bool, next_status: str, message: str) -> Dict:
        return {
            "allowed": allowed,
            "next_status": next_status,
            "message": message
        }
    
    def handle_defect_hold_transitions(self, current_status: str, location_type: str) -> Dict:
        # Hold 상태 체크 (명시적 해제 필요)
        if current_status == "Hold" and location_type not in ["HOLD"]:
            return self.next_status(False, current_status, "Hold 상태는 관리자 권한으로 명시적 해제가 필요합니다.")
        
        # 불량/보류 처리 우선
        if location_type == "DEFECT":
            if current_status == "Defect":
                # Defect 상태에서 다시 불량 리더기 태깅 시 해제
                # Deregistered 상태로 복귀
                return self.next_status(True, "Deregistered", "불량 해제되었습니다. (태그 회수)")
            return self.next_status(True, "Defect", "불량 처리되었습니다.")
        
        # HOLD 처리
        if location_type == "HOLD":
            # Hold 상태에서 다시 HOLD 리더기 태깅 시 해제
            # Hold 이전 상태로 복귀 (get_pre_hold_status 로 조회 필요)
            # 기본값: Stock (조회 실패 시)
            if current_status == "Hold":
                return self.next_status(True, "__RESTORE_PRE_HOLD__", "보류 해제되었습니다. (이전 상태로 복귀)")
            return self.next_status(True, "Hold", "보류 처리되었습니다.")

        return None  # Hold/Defect 처리 아님
    
    # IN 리더기 (공정 투입)
    def handle_in_transitions(self, current_status: str, location_type: str) -> Dict:
        if location_type != "IN":
            return None  # IN 처리 아님
        
        # 만차 팔레트 투입 (소비용)
        elif current_status == "Stock":
            return self.next_status(True, "Consuming", "소비 시작 (투입 완료)")

        # 소비 완료 (빈 팔레트 회수)
        elif current_status == "Consuming":
            return self.next_status(True, "Deregistered", "소비 완료 (빈 팔레트 회수)")
        else:
            return self.next_status(False, current_status, f"IN 위치에서 '{current_status}' 상태는 처리할 수 없습니다.")
    
    # OUT 리더기 (공정 완료)
    def handle_out_transitions(
        self, 
        current_status: str, 
        location_type: str, 
        process_code: str, 
        is_first_process: bool, 
        is_final_product: bool
    ) -> Dict:
        if location_type != "OUT":
            return None  # OUT 처리 아님

        # 첫 공정 특수 처리 (DB에서 is_first_process로 판단)
        if is_first_process:
            # 첫 공정에서 빈 팔레트 → 바로 생산 시작
            if current_status in ["Empty", "Generated"]:
                return self.next_status(True, "Producing", f"{process_code} 생산 시작")
            # 첫 공정 생산 완료 → Stock
            elif current_status == "Producing":
                return self.next_status(True, "Stock", f"{process_code} 생산 완료 (재고 적재)")
            # 이미 재고 상태 (수동 LOT 연결 후 OUT 스캔한 경우 idempotent)
            elif current_status == "Stock":
                return self.next_status(True, "Stock", "이미 재고 상태입니다. (생산 완료 확인)")

        # 이미 재고 상태 (수동으로 LOT 연결 후 스캔한 경우 idempotent 처리)
        elif current_status == "Stock":
                return self.next_status(True, "Stock", "이미 재고 상태입니다. (생산 완료 확인)")

        # 생산 완료
        if current_status == "Producing":
            if is_final_product:
                return self.next_status(True, "Finished", "완제품 생산 완료")
            else:
                return self.next_status(True, "Stock", "중간품 생산 완료 (재고 적재)")

        # 빈 팔레트 OUT → 생산 시작
        elif current_status in ["Empty", "Generated"]:
            return self.next_status(True, "Producing", "생산 시작 (적재용 팔레트)")
        else:
            return self.next_status(False, current_status, f"OUT 위치에서 '{current_status}' 상태는 처리할 수 없습니다.")

    def handle_finish_return_transitions(self, current_status: str, location_type: str) -> Dict:
        # 6. FINISH/RETURN 리더기 (완제품 출하/빈 팔레트 회수)
        if location_type not in ["FINISH", "RETURN"]:
            return   # FINISH/RETURN 처리 아님

        if current_status == "Finished":
            return self.next_status(True, "Deregistered", "완제품 출하 완료 (태그 회수)")

        elif current_status in ["Empty", "Generated"]:
            return self.next_status(True, "Deregistered", "빈 팔레트 회수 완료")

        else:
            return self.next_status(False, current_status, f"RETURN 위치에서 '{current_status}' 상태는 처리할 수 없습니다.")
                
    def handle_reg_transitions(self, current_status: str, location_type: str) -> Dict:
        # REG 리더기 (태그 등록)
        if location_type != "REG":
            return None  # REG 처리 아님

        if current_status == "Deregistered":
            return self.next_status(True, "Generated", "태그 등록 완료 (빈 팔레트 상태)")
        

        else:
            return self.next_status(False, current_status, f"REG 위치에서 '{current_status}' 상태는 처리할 수 없습니다.")

    def get_next_state(
        self, 
        current_status: str, 
        process_code: str, 
        location_type: str,
        is_final_product: bool = False,
        is_first_process: bool = False  # DB에서 가져온 첫 공정 여부
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

        # 불량/보류 처리
        result = self.handle_defect_hold_transitions(current_status, location_type)
        if result is not None:
            return result
        
        # IN 리더기 처리
        result = self.handle_in_transitions(current_status, location_type)
        if result is not None:
            return result
        
        # OUT 리더기 처리
        result = self.handle_out_transitions(current_status, location_type, process_code, is_first_process, is_final_product)
        if result is not None:
            return result
        
        # REG 리더기 처리
        result = self.handle_reg_transitions(current_status, location_type)
        if result is not None:
            return result

        # FINISH/RETURN 리더기 처리
        result = self.handle_finish_return_transitions(current_status, location_type)
        if result is not None:
            return result
        
        
        # 매칭되는 규칙이 없음
        return self.next_status(False, current_status, "해당 위치에서 상태 전이가 불가능합니다.")
