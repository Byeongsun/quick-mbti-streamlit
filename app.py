"""
Quick-MBTI: 빠르게 MBTI를 알려주는 웹 애플리케이션
리팩토링된 메인 애플리케이션
"""

import streamlit as st
from src.config import AppConfig
from src.mbti_analyzer import MBTIAnalyzer
from src.question_manager import QuestionManager
from src.ui_components import UIComponents
from src.utils import StateManager


class MBTIApp:
    def __init__(self):
        self.config = AppConfig()
        self.ui = UIComponents()
        self.state_manager = StateManager()
        self.question_manager = QuestionManager()
        self.mbti_analyzer = MBTIAnalyzer()
        
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
            self.ui.render_results(model, unresolved_axes, current_answers, self.config)
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