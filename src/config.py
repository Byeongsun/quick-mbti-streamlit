"""
설정 관리 모듈
상수와 설정값들을 중앙집중식으로 관리
"""

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
    
    # 질문 개수 설정
    BASE_QUESTIONS_PER_AXIS = 2
    ADDITIONAL_QUESTIONS_PER_AXIS = 2
    MAX_QUESTIONS_PER_AXIS = 6