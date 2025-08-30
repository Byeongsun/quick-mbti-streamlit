"""
UI 컴포넌트 모듈
사용자 인터페이스 렌더링 로직을 담당
"""

import streamlit as st
from typing import Dict, List, Any, Callable
from src.config import AppConfig


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
                      answers: List[Dict[str, Any]], config: AppConfig):
        """결과 화면 렌더링"""
        from src.mbti_analyzer import MBTIAnalyzer
        analyzer = MBTIAnalyzer()
        
        # MBTI 타입 표시
        display_type = analyzer.format_type_with_unresolved(model, unresolved_axes)
        
        st.subheader("결과")
        st.markdown(f"<h2 style='text-align: center; color: #1f77b4;'>{display_type}</h2>", 
                   unsafe_allow_html=True)
        
        # 상세 결과 표시
        self._render_detailed_results(model, config, analyzer)
        
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
        
    def _render_detailed_results(self, model: Dict[str, Any], config: AppConfig, 
                               analyzer):
        """상세 결과 표시"""
        st.subheader("📊 상세 결과")
        
        for axis in config.AXES:
            pole_a, pole_b = config.POLES[axis]
            count_a = model["count"][pole_a]
            count_b = model["count"][pole_b]
            total = model["totals"][axis]
            
            if total > 0:
                strength = analyzer.get_axis_preference_strength(axis, model)
                
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
                    
                st.write(f"**{axis}축**: {dominant} ({percentage:.1f}%) - {strength}")
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
                
    def render_progress_indicator(self, current_answered: int, total_questions: int):
        """진행률 표시"""
        if total_questions > 0:
            progress = current_answered / total_questions
            st.progress(progress)
            st.write(f"진행률: {current_answered}/{total_questions} "
                    f"({progress * 100:.1f}%)")
                    
    def render_error_message(self, message: str, error_type: str = "error"):
        """에러 메시지 렌더링"""
        if error_type == "error":
            st.error(message)
        elif error_type == "warning":
            st.warning(message)
        elif error_type == "info":
            st.info(message)
        else:
            st.write(message)
            
    def render_loading_spinner(self, text: str = "처리 중..."):
        """로딩 스피너 표시"""
        with st.spinner(text):
            pass