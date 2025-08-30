"""
Quick-MBTI: 빠르게 MBTI를 알려주는 웹 애플리케이션
리팩토링된 메인 애플리케이션
"""

import json
import random
import streamlit as st
from typing import Dict, List, Any, Set, Callable

# ----------------------- 설정 클래스 -----------------------
class AppConfig:
    """애플리케이션 설정 클래스"""
    
    PAGE_TITLE = "Quick-MBTI : 빠르게 MBTI를 알려줍니다"
    QUESTIONS_FILE = "questions_bank.json"
    
    AXES = ["EI", "SN", "TF", "JP"]
    
    POLES = {
        "EI": ("E", "I"),
        "SN": ("S", "N"),
        "TF": ("T", "F"),
        "JP": ("J", "P"),
    }
    
    COMMON_TIPS = [
        "생활: 에너지 패턴을 이해하고 휴식 규칙을 마련하세요.",
        "일: 강점 역할을 명확히 하고 협업 방식을 합의하세요.",
        "인간관계: 기대·경계를 공유하고 피드백을 정례화하세요.",
        "학습: 목표를 단계로 나눠 진행률을 가시화하세요.",
    ]
    
    MEANINGS = [
        ("E (Extraversion, 외향)", "사람들과의 교류·활동에서 에너지를 얻고, 외부 자극에 적극적으로 반응함"),
        ("I (Introversion, 내향)", "고요한 시간과 혼자만의 몰입에서 에너지를 회복하고, 신중한 내적 성찰을 선호함"),
        ("S (Sensing, 감각)", "현재의 구체적 사실·경험을 중시하고, 실용적이고 현실적인 정보에 신뢰를 둠"),
        ("N (Intuition, 직관)", "패턴·가능성과 같은 추상적 연결을 중시하고, 미래지향적 아이디어를 선호함"),
        ("T (Thinking, 사고)", "논리·일관성·원칙에 따라 판단하고, 공정한 기준을 우선함"),
        ("F (Feeling, 감정)", "사람·가치·관계의 조화를 중시하고, 공감과 배려를 판단에 반영함"),
        ("J (Judging, 판단)", "계획적·체계적으로 일을 정리하고, 마감과 규칙을 선호함"),
        ("P (Perceiving, 인식)", "상황에 맞춰 유연하게 적응하며, 열린 선택지를 유지하는 것을 선호함"),
    ]
    
    BASE_QUESTIONS_PER_AXIS = 2
    ADDITIONAL_QUESTIONS_PER_AXIS = 2
    MAX_QUESTIONS_PER_AXIS = 6

# ----------------------- MBTI 분석기 -----------------------
class MBTIAnalyzer:
    """MBTI 분석 클래스"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
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
        """기본 질문 후 추가 질문이 필요한지 판단"""
        return model["totals"][axis] == 2 and model["diff"][axis] == 0
        
    def is_unresolved_after_max(self, axis: str, model: Dict[str, Any]) -> bool:
        """최대 질문 수 후에도 미해결인지 판단"""
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

# ----------------------- 질문 관리자 -----------------------
class QuestionManager:
    """질문 관리 클래스"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
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

# ----------------------- UI 컴포넌트 -----------------------
class UIComponents:
    """UI 컴포넌트 클래스"""
    
    def render_question(self, question: Dict[str, Any], 
                       answer_callback: Callable[[str, Dict[str, Any]], None]):
        """개별 질문 렌더링"""
        st.markdown(f"**{question['prompt']}**")
        
        col1, col2 = st.columns(2)
        
        question_id = question["id"]
        
        # A 선택지
        if col1.button(f"① {question['A']['label']}", key=f"{question_id}_A"):
            answer_data = {
                "axis": question["axis"],
                "value": question["A"]["value"],
                "label": question["A"]["label"],
                "prompt": question["prompt"],
                "is_extra": question.get("is_extra", False)
            }
            answer_callback(question_id, answer_data)
            
        # B 선택지
        if col2.button(f"② {question['B']['label']}", key=f"{question_id}_B"):
            answer_data = {
                "axis": question["axis"],
                "value": question["B"]["value"],
                "label": question["B"]["label"],
                "prompt": question["prompt"],
                "is_extra": question.get("is_extra", False)
            }
            answer_callback(question_id, answer_data)
            
    def render_results(self, model: Dict[str, Any], unresolved_axes: List[str], 
                      answers: List[Dict[str, Any]], config: AppConfig, analyzer: MBTIAnalyzer):
        """결과 화면 렌더링"""
        # MBTI 타입 표시
        display_type = analyzer.format_type_with_unresolved(model, unresolved_axes)
        
        st.subheader("결과")
        st.markdown(f"<h2 style='text-align: center; color: #1f77b4;'>{display_type}</h2>", 
                   unsafe_allow_html=True)
        
        # 상세 결과 표시
        self._render_detailed_results(model, config)
        
        # 일반적인 팁 표시
        st.subheader("💡 일반적인 팁")
        for tip in config.COMMON_TIPS:
            st.write(f"• {tip}")
            
        # MBTI 의미 설명
        st.subheader("📚 MBTI 의미")
        for meaning, description in config.MEANINGS:
            st.write(f"**{meaning}**: {description}")
            
        # 응답 로그 표시
        self._render_answer_log(answers)
        
    def _render_detailed_results(self, model: Dict[str, Any], config: AppConfig):
        """상세 결과 표시"""
        st.subheader("📊 상세 결과")
        
        for axis in config.AXES:
            pole_a, pole_b = config.POLES[axis]
            count_a = model["count"][pole_a]
            count_b = model["count"][pole_b]
            total = model["totals"][axis]
            
            if total > 0:
                # 우세한 극점 결정
                if count_a > count_b:
                    dominant = pole_a
                    percentage = (count_a / total) * 100
                elif count_b > count_a:
                    dominant = pole_b
                    percentage = (count_b / total) * 100
                else:
                    dominant = "동점"
                    percentage = 50
                    
                st.write(f"**{axis}축**: {dominant} ({percentage:.1f}%)")
            else:
                st.write(f"**{axis}축**: 측정 안됨")
                
    def _render_answer_log(self, answers: List[Dict[str, Any]]):
        """응답 로그 렌더링"""
        st.subheader("📝 응답 로그")
        
        with st.expander("응답 상세 보기", expanded=False):
            for i, answer in enumerate(answers, start=1):
                extra_tag = "추가 " if answer.get("is_extra") else ""
                
                st.write(f"**{i}) [{answer['axis']}] {extra_tag}{answer['prompt']}**")
                st.write(f"   → 선택: {answer['label']} ({answer['value']})")
                st.write("")

# ----------------------- 상태 관리자 -----------------------
class StateManager:
    """세션 상태 관리 클래스"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
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

# ----------------------- 메인 애플리케이션 -----------------------
class MBTIApp:
    def __init__(self):
        self.config = AppConfig()
        self.ui = UIComponents()
        self.state_manager = StateManager(self.config)
        self.question_manager = QuestionManager(self.config)
        self.mbti_analyzer = MBTIAnalyzer(self.config)
        
    def setup_page(self):
        """페이지 기본 설정"""
        st.set_page_config(
            page_title=self.config.PAGE_TITLE, 
            layout="centered"
        )
        
    def initialize_session_state(self):
        """세션 상태 초기화"""
        if "mode" not in st.session_state:
            st.session_state.mode = "general"
        if "base" not in st.session_state:
            self.state_manager.reset_state()
            
    def handle_mode_change(self):
        """모드 변경 처리"""
        new_mode = "general" if st.session_state._aud.startswith("일반") else "senior"
        if st.session_state.mode != new_mode:
            st.session_state.mode = new_mode
            self.state_manager.reset_state()
            
    def render_mode_selection(self):
        """출제 범위 선택 UI 렌더링"""
        st.radio(
            "출제 범위 선택",
            options=["일반", "어르신(65세 이상)"],
            index=0 if st.session_state.mode == "general" else 1,
            horizontal=True,
            key="_aud",
            on_change=self.handle_mode_change
        )
        
    def setup_initial_questions(self):
        """초기 질문 설정"""
        if not st.session_state.base:
            try:
                questions_data = self.question_manager.load_questions()
                filtered_bank = self.question_manager.filter_by_audience(
                    questions_data, st.session_state.mode
                )
                
                base_questions = self.question_manager.generate_base_questions(filtered_bank)
                st.session_state.base = base_questions["questions"]
                st.session_state.base_ids = base_questions["ids"]
                st.session_state.used = base_questions["used_prompts"]
                
            except Exception as e:
                st.error(f"질문을 불러오는데 실패했습니다: {e}")
                st.stop()
                
    def render_questions(self):
        """질문 렌더링"""
        st.header("문항")
        
        all_questions = st.session_state.base + st.session_state.extra
        for question in all_questions:
            self.ui.render_question(question, self._handle_answer)
            
    def _handle_answer(self, question_id: str, answer_data: dict):
        """답변 처리"""
        st.session_state.answers[question_id] = answer_data
        
    def handle_additional_questions(self):
        """추가 질문 처리"""
        base_answered = sum(1 for qid in st.session_state.base_ids 
                          if qid in st.session_state.answers)
        
        # 기본 8문항 완료 후 tie 축 처리
        if base_answered == 8 and not st.session_state.base_done:
            current_answers = list(st.session_state.answers.values())
            model = self.mbti_analyzer.compute_mbti(current_answers)
            
            questions_data = self.question_manager.load_questions()
            filtered_bank = self.question_manager.filter_by_audience(
                questions_data, st.session_state.mode
            )
            
            # tie 축에 대한 추가 질문 생성
            for axis in self.config.AXES:
                if self.mbti_analyzer.needs_more_questions_after_base(axis, model):
                    additional_questions = self.question_manager.generate_additional_questions(
                        filtered_bank, axis, st.session_state.used, count=2
                    )
                    st.session_state.extra.extend(additional_questions)
                    
            st.session_state.base_done = True
            
    def check_completion_and_show_results(self):
        """완료 확인 및 결과 표시"""
        all_ids = st.session_state.base_ids + [q["id"] for q in st.session_state.extra]
        all_answered = all(qid in st.session_state.answers for qid in all_ids)
        base_answered = sum(1 for qid in st.session_state.base_ids 
                          if qid in st.session_state.answers)
        
        if base_answered == 8 and all_answered:
            current_answers = list(st.session_state.answers.values())
            model = self.mbti_analyzer.compute_mbti(current_answers)
            unresolved_axes = self.mbti_analyzer.get_unresolved_axes(model)
            
            # 결과 표시
            self.ui.render_results(model, unresolved_axes, current_answers, self.config, self.mbti_analyzer)
            st.stop()
            
    def run(self):
        """메인 애플리케이션 실행"""
        self.setup_page()
        self.initialize_session_state()
        self.render_mode_selection()
        self.setup_initial_questions()
        self.render_questions()
        self.handle_additional_questions()
        self.check_completion_and_show_results()


if __name__ == "__main__":
    app = MBTIApp()
    app.run()