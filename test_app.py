# test_app.py
"""
간단한 앱 테스트 파일
"""

import unittest
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# app.py에서 클래스들을 import
from app import AppConfig, MBTIAnalyzer, QuestionManager, UIComponents, StateManager


class TestMBTIAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.config = AppConfig()
        self.analyzer = MBTIAnalyzer(self.config)
        
    def test_compute_mbti_simple(self):
        """기본 MBTI 계산 테스트"""
        answers = [
            {"axis": "EI", "value": "E"},
            {"axis": "EI", "value": "E"},
            {"axis": "SN", "value": "N"},
            {"axis": "SN", "value": "N"},  # S를 N으로 수정
            {"axis": "TF", "value": "T"},
            {"axis": "TF", "value": "T"},
            {"axis": "JP", "value": "P"},
            {"axis": "JP", "value": "P"},
        ]
        
        result = self.analyzer.compute_mbti(answers)
        
        self.assertEqual(result["type"], "ENTP")
        self.assertEqual(result["count"]["E"], 2)
        self.assertEqual(result["count"]["I"], 0)
        self.assertEqual(result["count"]["N"], 2)  # N 카운트 확인 추가
        self.assertEqual(result["count"]["T"], 2)  # T 카운트 확인 추가
        self.assertEqual(result["count"]["P"], 2)  # P 카운트 확인 추가
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
        self.assertTrue(result["type"].startswith("E") or result["type"].startswith("I"))
        self.assertEqual(result["diff"]["EI"], 0)
        
    def test_needs_more_questions_after_base(self):
        """기본 질문 후 추가 질문 필요성 판단 테스트"""
        model = {
            "totals": {"EI": 2, "SN": 2, "TF": 2, "JP": 2},
            "diff": {"EI": 0, "SN": 2, "TF": 1, "JP": 0}
        }
        
        # EI축과 JP축만 동점이므로 추가 질문 필요
        self.assertTrue(self.analyzer.needs_more_questions_after_base("EI", model))
        self.assertFalse(self.analyzer.needs_more_questions_after_base("SN", model))
        self.assertFalse(self.analyzer.needs_more_questions_after_base("TF", model))
        self.assertTrue(self.analyzer.needs_more_questions_after_base("JP", model))
        
    def test_format_type_with_unresolved(self):
        """미해결 축 포함 타입 포맷팅 테스트"""
        model = {
            "count": {"E": 3, "I": 3, "S": 4, "N": 2, "T": 3, "F": 1, "J": 2, "P": 2}
        }
        unresolved_axes = ["EI", "JP"]
        
        result = self.analyzer.format_type_with_unresolved(model, unresolved_axes)
        # EI는 동점이므로 (E/I), SN은 S가 우세, TF는 T가 우세, JP는 동점이므로 (J/P)
        self.assertEqual(result, "(E/I)ST(J/P)")


class TestQuestionManager(unittest.TestCase):
    
    def setUp(self):
        self.config = AppConfig()
        self.manager = QuestionManager(self.config)
        
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
            ],
            "TF": [
                {
                    "audience": "general",
                    "prompt": "TF 질문 1",
                    "A": {"label": "선택지 A", "value": "T"},
                    "B": {"label": "선택지 B", "value": "F"}
                },
                {
                    "audience": "general",
                    "prompt": "TF 질문 2",
                    "A": {"label": "선택지 A", "value": "T"},
                    "B": {"label": "선택지 B", "value": "F"}
                }
            ],
            "JP": [
                {
                    "audience": "general",
                    "prompt": "JP 질문 1",
                    "A": {"label": "선택지 A", "value": "J"},
                    "B": {"label": "선택지 B", "value": "P"}
                },
                {
                    "audience": "general",
                    "prompt": "JP 질문 2",
                    "A": {"label": "선택지 A", "value": "J"},
                    "B": {"label": "선택지 B", "value": "P"}
                }
            ]
        }
        
    def test_filter_by_audience_general(self):
        """일반 대상 필터링 테스트"""
        filtered = self.manager.filter_by_audience(self.test_data, "general")
        
        # EI축: general 2개
        self.assertEqual(len(filtered["EI"]), 2)
        # SN축: both 1개, audience 없는 것 1개
        self.assertEqual(len(filtered["SN"]), 2)
        # TF축: general 2개
        self.assertEqual(len(filtered["TF"]), 2)
        # JP축: general 2개
        self.assertEqual(len(filtered["JP"]), 2)
        
    def test_filter_by_audience_senior(self):
        """시니어 대상 필터링 테스트"""
        filtered = self.manager.filter_by_audience(self.test_data, "senior")
        
        # EI축: senior 1개, audience 없는 것 0개
        self.assertEqual(len(filtered["EI"]), 1)
        # SN축: both 1개, audience 없는 것 1개  
        self.assertEqual(len(filtered["SN"]), 2)
        
    def test_generate_base_questions_success(self):
        """기본 질문 생성 성공 테스트"""
        filtered_data = self.manager.filter_by_audience(self.test_data, "general")
        
        result = self.manager.generate_base_questions(filtered_data)
        
        # 각 축당 2개씩 총 8개
        self.assertEqual(len(result["questions"]), 8)
        self.assertEqual(len(result["ids"]), 8)
        
        # 각 축별로 사용된 질문 확인
        for axis in self.config.AXES:
            self.assertIn(axis, result["used_prompts"])
            self.assertEqual(len(result["used_prompts"][axis]), 2)
            
    def test_generate_additional_questions(self):
        """추가 질문 생성 테스트"""
        filtered_data = self.manager.filter_by_audience(self.test_data, "general")
        used_prompts = {"EI": {"테스트 질문 1"}, "SN": set(), "TF": set(), "JP": set()}
        
        additional = self.manager.generate_additional_questions(
            filtered_data, "EI", used_prompts, count=1
        )
        
        # 1개 질문이 생성되어야 함
        self.assertEqual(len(additional), 1)
        self.assertEqual(additional[0]["axis"], "EI")
        self.assertTrue(additional[0]["is_extra"])


class TestAppConfig(unittest.TestCase):
    
    def test_config_values(self):
        """설정값 테스트"""
        config = AppConfig()
        
        self.assertEqual(len(config.AXES), 4)
        self.assertIn("EI", config.AXES)
        self.assertIn("SN", config.AXES)
        self.assertIn("TF", config.AXES)
        self.assertIn("JP", config.AXES)
        
        self.assertEqual(config.POLES["EI"], ("E", "I"))
        self.assertEqual(config.BASE_QUESTIONS_PER_AXIS, 2)
        
    def test_tips_and_meanings_exist(self):
        """팁과 의미 설명이 존재하는지 테스트"""
        config = AppConfig()
        
        self.assertGreater(len(config.COMMON_TIPS), 0)
        self.assertGreater(len(config.MEANINGS), 0)
        
        # 각 MBTI 차원에 대한 설명이 있는지 확인
        meaning_keys = [meaning[0] for meaning in config.MEANINGS]
        self.assertTrue(any("E (" in key for key in meaning_keys))
        self.assertTrue(any("I (" in key for key in meaning_keys))
        self.assertTrue(any("S (" in key for key in meaning_keys))
        self.assertTrue(any("N (" in key for key in meaning_keys))


class TestIntegration(unittest.TestCase):
    """통합 테스트"""
    
    def test_full_workflow_simulation(self):
        """전체 워크플로우 시뮬레이션 테스트"""
        config = AppConfig()
        analyzer = MBTIAnalyzer(config)
        
        # 시뮬레이션된 답변 (각 축당 2개씩, 모두 명확한 선호도)
        answers = [
            {"axis": "EI", "value": "E"},  # 외향
            {"axis": "EI", "value": "E"},
            {"axis": "SN", "value": "N"},  # 직관
            {"axis": "SN", "value": "N"}, 
            {"axis": "TF", "value": "F"},  # 감정
            {"axis": "TF", "value": "F"},
            {"axis": "JP", "value": "P"},  # 인식
            {"axis": "JP", "value": "P"},
        ]
        
        # MBTI 계산
        result = analyzer.compute_mbti(answers)
        
        # 결과 검증
        self.assertEqual(result["type"], "ENFP")
        self.assertEqual(result["count"]["E"], 2)
        self.assertEqual(result["count"]["N"], 2) 
        self.assertEqual(result["count"]["F"], 2)
        self.assertEqual(result["count"]["P"], 2)
        
        # 추가 질문이 필요하지 않음을 확인
        for axis in config.AXES:
            self.assertFalse(analyzer.needs_more_questions_after_base(axis, result))
            
    def test_tie_situation_workflow(self):
        """동점 상황 워크플로우 테스트"""
        config = AppConfig()
        analyzer = MBTIAnalyzer(config)
        
        # 모든 축에서 동점인 답변
        answers = [
            {"axis": "EI", "value": "E"},
            {"axis": "EI", "value": "I"},
            {"axis": "SN", "value": "S"},
            {"axis": "SN", "value": "N"}, 
            {"axis": "TF", "value": "T"},
            {"axis": "TF", "value": "F"},
            {"axis": "JP", "value": "J"},
            {"axis": "JP", "value": "P"},
        ]
        
        result = analyzer.compute_mbti(answers)
        
        # 모든 축에서 추가 질문이 필요함을 확인
        for axis in config.AXES:
            self.assertTrue(analyzer.needs_more_questions_after_base(axis, result))
            
        # 기본값으로 ESTJ가 나와야 함 (각 축의 첫 번째 극점)
        self.assertEqual(result["type"], "ESTJ")


if __name__ == "__main__":
    # 테스트 실행
    unittest.main(verbosity=2)