"""
MBTI 분석 모듈
MBTI 결과 계산 및 분석 로직을 담당
"""

from typing import List, Dict, Any
from src.config import AppConfig


class MBTIAnalyzer:
    """MBTI 분석 클래스"""
    
    def __init__(self):
        self.config = AppConfig()
        
    def compute_mbti(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """답변 리스트를 기반으로 MBTI 결과 계산"""
        # 각 극점별 카운트 초기화
        count = {pole: 0 for poles in self.config.POLES.values() for pole in poles}
        
        # 각 축별 총 답변 수 초기화
        totals = {axis: 0 for axis in self.config.AXES}
        
        # 답변 카운팅
        for answer in answers:
            value = answer["value"]
            axis = answer["axis"]
            
            if value in count:
                count[value] += 1
            totals[axis] += 1
            
        # 각 축별 차이 계산
        diff = {}
        for axis in self.config.AXES:
            pole_a, pole_b = self.config.POLES[axis]
            diff[axis] = abs(count[pole_a] - count[pole_b])
            
        # MBTI 타입 결정
        mbti_type = ""
        for axis in self.config.AXES:
            pole_a, pole_b = self.config.POLES[axis]
            
            if count[pole_a] > count[pole_b]:
                mbti_type += pole_a
            elif count[pole_a] < count[pole_b]:
                mbti_type += pole_b
            else:
                # 동점일 경우 기본값 사용
                mbti_type += pole_a
                
        return {
            "type": mbti_type,
            "count": count,
            "totals": totals,
            "diff": diff
        }
        
    def needs_more_questions_after_base(self, axis: str, model: Dict[str, Any]) -> bool:
        """기본 질문 후 추가 질문이 필요한지 판단 (2문항 후 동점)"""
        return model["totals"][axis] == 2 and model["diff"][axis] == 0
        
    def needs_more_questions_after_additional(self, axis: str, model: Dict[str, Any]) -> bool:
        """추가 질문 후 더 많은 질문이 필요한지 판단 (4문항 후 동점)"""
        return model["totals"][axis] == 4 and model["diff"][axis] == 0
        
    def is_unresolved_after_max(self, axis: str, model: Dict[str, Any]) -> bool:
        """최대 질문 수 후에도 미해결인지 판단 (6문항 후 동점)"""
        return model["totals"][axis] == 6 and model["diff"][axis] == 0
        
    def get_unresolved_axes(self, model: Dict[str, Any]) -> List[str]:
        """미해결 축들 반환"""
        return [axis for axis in self.config.AXES 
                if self.is_unresolved_after_max(axis, model)]
        
    def format_type_with_unresolved(self, model: Dict[str, Any], 
                                  unresolved_axes: List[str]) -> str:
        """미해결 축을 포함한 MBTI 타입 포맷팅"""
        # 각 축별 우세한 극점 결정
        leading_poles = {}
        for axis in self.config.AXES:
            pole_a, pole_b = self.config.POLES[axis]
            leading_poles[axis] = (
                pole_a if model["count"][pole_a] >= model["count"][pole_b] else pole_b
            )
            
        # 결과 문자열 생성
        result_parts = []
        for axis in self.config.AXES:
            if axis in unresolved_axes:
                pole_a, pole_b = self.config.POLES[axis]
                result_parts.append(f"({pole_a}/{pole_b})")
            else:
                result_parts.append(leading_poles[axis])
                
        return "".join(result_parts)
        
    def get_axis_preference_strength(self, axis: str, model: Dict[str, Any]) -> str:
        """축별 선호도 강도 반환"""
        diff = model["diff"][axis]
        total = model["totals"][axis]
        
        if total == 0:
            return "측정 불가"
            
        strength_ratio = diff / total
        
        if strength_ratio >= 0.6:
            return "강함"
        elif strength_ratio >= 0.3:
            return "보통"
        elif strength_ratio > 0:
            return "약함"
        else:
            return "동점"