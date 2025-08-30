"""
질문 관리 모듈
질문 로드, 필터링, 선택 로직을 담당
"""

import json
import random
from typing import Dict, List, Any, Set
from src.config import AppConfig


class QuestionManager:
    """질문 관리 클래스"""
    
    def __init__(self):
        self.config = AppConfig()
        
    def load_questions(self) -> Dict[str, List[Dict[str, Any]]]:
        """질문 데이터 로드"""
        try:
            with open(self.config.QUESTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.config.QUESTIONS_FILE} 파일을 찾을 수 없습니다.")
        except json.JSONDecodeError:
            raise ValueError(f"{self.config.QUESTIONS_FILE} 파일 형식이 올바르지 않습니다.")
        except Exception as e:
            raise Exception(f"질문 파일 로드 중 오류 발생: {e}")
            
    def filter_by_audience(self, questions_data: Dict[str, List[Dict[str, Any]]], 
                          audience: str) -> Dict[str, List[Dict[str, Any]]]:
        """대상 그룹별로 질문 필터링"""
        filtered = {axis: [] for axis in self.config.AXES}
        
        for axis in self.config.AXES:
            for question in questions_data.get(axis, []):
                question_audience = question.get("audience")
                
                # audience가 없거나, both거나, 현재 모드와 일치하면 포함
                if (not question_audience or 
                    question_audience == "both" or 
                    question_audience == audience):
                    filtered[axis].append(question)
                    
        return filtered
        
    def _sample_random_questions(self, questions: List[Dict[str, Any]], 
                                count: int) -> List[Dict[str, Any]]:
        """질문 리스트에서 랜덤하게 선택"""
        if len(questions) < count:
            # 질문이 부족하면 중복 허용
            return random.choices(questions, k=count) if questions else []
        
        return random.sample(questions, count)
        
    def generate_base_questions(self, filtered_bank: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """기본 질문 생성 (각 축당 2개)"""
        base_questions = []
        base_ids = []
        used_prompts = {axis: set() for axis in self.config.AXES}
        
        for axis in self.config.AXES:
            axis_questions = filtered_bank.get(axis, [])
            
            if len(axis_questions) < self.config.BASE_QUESTIONS_PER_AXIS:
                raise ValueError(f"{axis} 축의 질문이 {self.config.BASE_QUESTIONS_PER_AXIS}개 미만입니다.")
                
            selected_questions = self._sample_random_questions(
                axis_questions, self.config.BASE_QUESTIONS_PER_AXIS
            )
            
            for i, question_data in enumerate(selected_questions, 1):
                question_id = f"base_{axis}_{i}"
                question = {
                    "id": question_id,
                    "axis": axis,
                    **question_data
                }
                
                base_questions.append(question)
                base_ids.append(question_id)
                used_prompts[axis].add(question_data["prompt"])
                
        # 질문 순서 섞기
        random.shuffle(base_questions)
        
        return {
            "questions": base_questions,
            "ids": base_ids,
            "used_prompts": used_prompts
        }
        
    def generate_additional_questions(self, filtered_bank: Dict[str, List[Dict[str, Any]]], 
                                    axis: str, used_prompts: Dict[str, Set[str]], 
                                    count: int = 2) -> List[Dict[str, Any]]:
        """추가 질문 생성"""
        axis_questions = filtered_bank.get(axis, [])
        
        # 사용하지 않은 질문들 필터링
        available_questions = [
            q for q in axis_questions 
            if q["prompt"] not in used_prompts[axis]
        ]
        
        if not available_questions:
            # 사용 가능한 질문이 없으면 빈 리스트 반환
            return []
            
        selected_questions = self._sample_random_questions(available_questions, count)
        additional_questions = []
        
        for question_data in selected_questions:
            question_id = f"extra_{axis}_{random.randint(1, 10**9)}"
            question = {
                "id": question_id,
                "axis": axis,
                "is_extra": True,
                **question_data
            }
            
            additional_questions.append(question)
            used_prompts[axis].add(question_data["prompt"])
            
        return additional_questions
        
    def validate_question_bank(self, questions_data: Dict[str, List[Dict[str, Any]]], 
                             audience: str) -> bool:
        """질문 데이터 유효성 검사"""
        filtered_bank = self.filter_by_audience(questions_data, audience)
        
        for axis in self.config.AXES:
            axis_questions = filtered_bank.get(axis, [])
            
            if len(axis_questions) < self.config.BASE_QUESTIONS_PER_AXIS:
                return False
                
            # 각 질문의 필수 필드 검사
            for question in axis_questions:
                required_fields = ["prompt", "A", "B"]
                if not all(field in question for field in required_fields):
                    return False
                    
                # 선택지 구조 검사
                for choice in ["A", "B"]:
                    choice_data = question[choice]
                    if not isinstance(choice_data, dict):
                        return False
                    if not all(field in choice_data for field in ["label", "value"]):
                        return False
                        
        return True