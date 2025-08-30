# tests/test_mbti_analyzer.py
"""
MBTI 분석기 테스트
"""

import unittest
from src.mbti_analyzer import MBTIAnalyzer


class TestMBTIAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = MBTIAnalyzer()
        
    def test_compute_mbti_simple(self):
        """기본 MBTI 계산 테스트"""
        answers = [
            {"axis": "EI", "value": "E"},
            {"axis": "EI", "value": "E"},
            {"axis": "SN", "value": "N"},
            {"axis": "SN", "value": "S"},
            {"axis": "TF", "value": "T"},
            {"axis": "TF", "value": "T"},
            {"axis": "JP", "value": "P"},
            {"axis": "JP", "value": "P"},
        ]
        
        result = self.analyzer.compute_mbti(answers)
        
        self.assertEqual(result["type"], "ENTP")
        self.assertEqual(result["count"]["E"], 2)
        self.assertEqual(result["count"]["I"], 0)
        self.assertEqual(result["diff"]["EI"], 2)
        
    def test_compute_mbti_tie(self):
        """동점 상황 MBTI 계산 테스트"""
        answers = [
            {"axis": "EI", "value": "E"},
            {"axis": "EI", "value": "I"},
            {"axis": "SN", "value": "S"},
            {"axis": "SN", "value": "S"},
        ]
        
        result = self.analyzer.compute_mbti(answers)
        
        # 동점일 경우 첫 번째 극점이 기본값
        self.assertEqual(result["type"], "ES")
        self.assertEqual(result["diff"]["EI"], 0)
        
    def test_needs_more_questions_after_base(self):
        """기본 질문 후 추가 질문 필요성 판단 테스트"""
        model = {
            "totals": {"EI": 2},
            "diff": {"EI": 0}
        }
        
        self.assertTrue(self.analyzer.needs_more_questions_after_base("EI", model))
        
        model["diff"]["EI"] = 2
        self.assertFalse(self.analyzer.needs_more_questions_after_base("EI", model))
        
    def test_format_type_with_unresolved(self):
        """미해결 축 포함 타입 포맷팅 테스트"""
        model = {
            "count": {"E": 2, "I": 2, "S": 3, "N": 1, "T": 2, "F": 0, "J": 1, "P": 1}
        }
        unresolved_axes = ["EI", "JP"]
        
        result = self.analyzer.format_type_with_unresolved(model, unresolved_axes)
        self.assertEqual(result, "(E/I)ST(J/P)")


# tests/test_question_manager.py
"""
질문 관리자 테스트
"""

import unittest
import tempfile
import json
import os
from src.question_manager import QuestionManager


class TestQuestionManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = QuestionManager()
        
        # 테스트용 임시 질문 데이터
        self.test_data = {
            "EI": [
                {
                    "audience": "general",
                    "prompt": "테스트 질문 1",
                    "A": {"label": "선택지 A", "value": "E"},
                    "B": {"label": "선택지 B", "value": "I"}
                },
                {
                    "audience": "general", 
                    "prompt": "테스트 질문 2",
                    "A": {"label": "선택지 A", "value": "E"},
                    "B": {"label": "선택지 B", "value": "I"}
                },
                {
                    "audience": "senior",
                    "prompt": "시니어 질문 1", 
                    "A": {"label": "선택지 A", "value": "E"},
                    "B": {"label": "선택지 B", "value": "I"}
                }
            ],
            "SN": [
                {
                    "audience": "both",
                    "prompt": "공통 질문 1",
                    "A": {"label": "선택지 A", "value": "S"},
                    "B": {"label": "선택지 B", "value": "N"}
                },
                {
                    "prompt": "audience 없는 질문",
                    "A": {"label": "선택지 A", "value": "S"}, 
                    "B": {"label": "선택지 B", "value": "N"}
                }
            ]
        }
        
    def test_filter_by_audience_general(self):
        """일반 대상 필터링 테스트"""
        filtered = self.manager.filter_by_audience(self.test_data, "general")
        
        # EI축: general 2개, senior 0개
        self.assertEqual(len(filtered["EI"]), 2)
        # SN축: both 1개, audience 없는 것 1개
        self.assertEqual(len(filtered["SN"]), 2)
        
    def test_filter_by_audience_senior(self):
        """시니어 대상 필터링 테스트"""
        filtered = self.manager.filter_by_audience(self.test_data, "senior")
        
        # EI축: senior 1개, audience 없는 것 0개
        self.assertEqual(len(filtered["EI"]), 1)
        # SN축: both 1개, audience 없는 것 1개  
        self.assertEqual(len(filtered["SN"]), 2)
        
    def test_generate_base_questions(self):
        """기본 질문 생성 테스트"""
        # EI, SN 축만 있는 축소된 데이터로 테스트
        limited_data = {
            "EI": self.test_data["EI"][:2],  # 2개만
            "SN": self.test_data["SN"]      # 2개
        }
        
        # 설정을 EI, SN만으로 제한
        original_axes = self.manager.config.AXES
        self.manager.config.AXES = ["EI", "SN"]
        
        try:
            result = self.manager.generate_base_questions(limited_data)
            
            self.assertEqual(len(result["questions"]), 4)  # 각 축당 2개
            self.assertEqual(len(result["ids"]), 4)
            self.assertIn("EI", result["used_prompts"])
            self.assertIn("SN", result["used_prompts"])
            
        finally:
            # 원래 설정 복원
            self.manager.config.AXES = original_axes
            
    def test_validate_question_bank(self):
        """질문 데이터 유효성 검사 테스트"""
        # 유효한 데이터
        self.assertTrue(self.manager.validate_question_bank(self.test_data, "general"))
        
        # 불충분한 질문 개수
        insufficient_data = {"EI": [self.test_data["EI"][0]]}  # 1개만
        self.assertFalse(self.manager.validate_question_bank(insufficient_data, "general"))


# tests/test_utils.py  
"""
유틸리티 테스트
"""

import unittest
from src.utils import ValidationUtils, DataUtils


class TestValidationUtils(unittest.TestCase):
    
    def test_validate_answer_data_valid(self):
        """유효한 답변 데이터 검증 테스트"""
        valid_answer = {
            "axis": "EI",
            "value": "E", 
            "label": "외향적",
            "prompt": "테스트 질문"
        }
        
        self.assertTrue(ValidationUtils.validate_answer_data(valid_answer))
        
    def test_validate_answer_data_invalid(self):
        """무효한 답변 데이터 검증 테스트"""
        invalid_answer = {
            "axis": "EI",
            "value": "E"
            # label과 prompt 누락
        }
        
        self.assertFalse(ValidationUtils.validate_answer_data(invalid_answer))
        
    def test_validate_question_data_valid(self):
        """유효한 질문 데이터 검증 테스트"""
        valid_question = {
            "id": "test_1",
            "axis": "EI",
            "prompt": "테스트 질문",
            "A": {"label": "선택지 A", "value": "E"},
            "B": {"label": "선택지 B", "value": "I"}
        }
        
        self.assertTrue(ValidationUtils.validate_question_data(valid_question))


class TestDataUtils(unittest.TestCase):
    
    def test_calculate_axis_distribution(self):
        """축별 답변 분포 계산 테스트"""
        answers = [
            {"axis": "EI", "value": "E"},
            {"axis": "EI", "value": "E"}, 
            {"axis": "EI", "value": "I"},
            {"axis": "SN", "value": "S"},
        ]
        
        distribution = DataUtils.calculate_axis_distribution(answers)
        
        self.assertEqual(distribution["EI"]["E"], 2)
        self.assertEqual(distribution["EI"]["I"], 1) 
        self.assertEqual(distribution["EI"]["total"], 3)
        self.assertEqual(distribution["SN"]["S"], 1)
        self.assertEqual(distribution["SN"]["N"], 0)


if __name__ == "__main__":
    unittest.main()