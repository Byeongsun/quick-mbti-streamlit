"""
유틸리티 모듈
공통적으로 사용되는 헬퍼 함수들과 상태 관리 클래스
"""

import streamlit as st
from typing import Dict, List, Any, Set
from src.config import AppConfig


class StateManager:
    """세션 상태 관리 클래스"""
    
    def __init__(self):
        self.config = AppConfig()
        
    def reset_state(self):
        """세션 상태 초기화"""
        st.session_state.base = []
        st.session_state.base_ids = []
        st.session_state.used = {axis: set() for axis in self.config.AXES}
        st.session_state.answers = {}
        st.session_state.extra = []
        st.session_state.base_done = False
        st.session_state.result_ready = False
        st.session_state.unresolved_axes = []
        st.session_state.answer_log = []
        
    def get_current_progress(self) -> Dict[str, int]:
        """현재 진행 상황 반환"""
        base_answered = sum(1 for qid in st.session_state.base_ids 
                          if qid in st.session_state.answers)
        extra_answered = sum(1 for q in st.session_state.extra 
                           if q["id"] in st.session_state.answers)
        total_questions = len(st.session_state.base) + len(st.session_state.extra)
        
        return {
            "base_answered": base_answered,
            "extra_answered": extra_answered,
            "total_answered": base_answered + extra_answered,
            "total_questions": total_questions
        }
        
    def is_base_complete(self) -> bool:
        """기본 질문 완료 여부 확인"""
        base_answered = sum(1 for qid in st.session_state.base_ids 
                          if qid in st.session_state.answers)
        return base_answered == len(st.session_state.base_ids)
        
    def is_all_complete(self) -> bool:
        """모든 질문 완료 여부 확인"""
        all_ids = st.session_state.base_ids + [q["id"] for q in st.session_state.extra]
        return all(qid in st.session_state.answers for qid in all_ids)
        
    def get_answers_by_axis(self, axis: str) -> List[Dict[str, Any]]:
        """특정 축의 답변들 반환"""
        return [answer for answer in st.session_state.answers.values() 
                if answer["axis"] == axis]
                
    def save_state_to_cache(self) -> Dict[str, Any]:
        """현재 상태를 캐시용 딕셔너리로 저장"""
        return {
            "mode": st.session_state.mode,
            "answers": st.session_state.answers.copy(),
            "base_done": st.session_state.base_done
        }
        
    def load_state_from_cache(self, cached_state: Dict[str, Any]):
        """캐시된 상태를 복원"""
        if "mode" in cached_state:
            st.session_state.mode = cached_state["mode"]
        if "answers" in cached_state:
            st.session_state.answers = cached_state["answers"]
        if "base_done" in cached_state:
            st.session_state.base_done = cached_state["base_done"]


class ValidationUtils:
    """유효성 검사 유틸리티 클래스"""
    
    @staticmethod
    def validate_answer_data(answer_data: Dict[str, Any]) -> bool:
        """답변 데이터 유효성 검사"""
        required_fields = ["axis", "value", "label", "prompt"]
        return all(field in answer_data for field in required_fields)
        
    @staticmethod
    def validate_question_data(question_data: Dict[str, Any]) -> bool:
        """질문 데이터 유효성 검사"""
        required_fields = ["id", "axis", "prompt", "A", "B"]
        if not all(field in question_data for field in required_fields):
            return False
            
        # 선택지 유효성 검사
        for choice in ["A", "B"]:
            choice_data = question_data[choice]
            if not isinstance(choice_data, dict):
                return False
            if not all(field in choice_data for field in ["label", "value"]):
                return False
                
        return True
        
    @staticmethod
    def validate_session_state() -> List[str]:
        """세션 상태 유효성 검사 및 오류 메시지 반환"""
        errors = []
        
        required_session_keys = [
            "base", "base_ids", "used", "answers", "extra", 
            "base_done", "result_ready", "unresolved_axes"
        ]
        
        for key in required_session_keys:
            if key not in st.session_state:
                errors.append(f"세션 상태에 '{key}' 키가 없습니다.")
                
        return errors


class DataUtils:
    """데이터 처리 유틸리티 클래스"""
    
    @staticmethod
    def calculate_axis_distribution(answers: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """축별 답변 분포 계산"""
        config = AppConfig()
        distribution = {}
        
        for axis in config.AXES:
            pole_a, pole_b = config.POLES[axis]
            axis_answers = [a for a in answers if a["axis"] == axis]
            
            count_a = sum(1 for a in axis_answers if a["value"] == pole_a)
            count_b = sum(1 for a in axis_answers if a["value"] == pole_b)
            
            distribution[axis] = {
                pole_a: count_a,
                pole_b: count_b,
                "total": count_a + count_b
            }
            
        return distribution
        
    @staticmethod
    def get_axis_summary(answers: List[Dict[str, Any]]) -> Dict[str, str]:
        """축별 요약 정보 생성"""
        distribution = DataUtils.calculate_axis_distribution(answers)
        config = AppConfig()
        summary = {}
        
        for axis in config.AXES:
            pole_a, pole_b = config.POLES[axis]
            axis_data = distribution[axis]
            
            if axis_data["total"] == 0:
                summary[axis] = "측정 안됨"
            elif axis_data[pole_a] > axis_data[pole_b]:
                percentage = (axis_data[pole_a] / axis_data["total"]) * 100
                summary[axis] = f"{pole_a} ({percentage:.1f}%)"
            elif axis_data[pole_b] > axis_data[pole_a]:
                percentage = (axis_data[pole_b] / axis_data["total"]) * 100
                summary[axis] = f"{pole_b} ({percentage:.1f}%)"
            else:
                summary[axis] = "동점 (50.0%)"
                
        return summary
        
    @staticmethod
    def export_results_to_dict(model: Dict[str, Any], answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """결과를 내보내기 가능한 딕셔너리 형태로 변환"""
        return {
            "mbti_type": model["type"],
            "axis_counts": model["count"],
            "axis_totals": model["totals"],
            "axis_differences": model["diff"],
            "axis_summary": DataUtils.get_axis_summary(answers),
            "total_questions": len(answers),
            "answers": answers
        }


class LoggingUtils:
    """로깅 유틸리티 클래스"""
    
    @staticmethod
    def log_user_action(action_type: str, details: Dict[str, Any] = None):
        """사용자 액션 로깅 (개발/디버깅용)"""
        if "action_log" not in st.session_state:
            st.session_state.action_log = []
            
        log_entry = {
            "action_type": action_type,
            "timestamp": pd.Timestamp.now().isoformat() if 'pd' in globals() else "unknown",
            "details": details or {}
        }
        
        st.session_state.action_log.append(log_entry)
        
        # 로그가 너무 길어지면 오래된 항목 제거
        if len(st.session_state.action_log) > 100:
            st.session_state.action_log = st.session_state.action_log[-50:]
            
    @staticmethod
    def get_session_summary() -> Dict[str, Any]:
        """세션 요약 정보 반환"""
        return {
            "mode": getattr(st.session_state, "mode", "unknown"),
            "base_questions_count": len(getattr(st.session_state, "base", [])),
            "extra_questions_count": len(getattr(st.session_state, "extra", [])),
            "answers_count": len(getattr(st.session_state, "answers", {})),
            "base_done": getattr(st.session_state, "base_done", False),
            "result_ready": getattr(st.session_state, "result_ready", False)
        }