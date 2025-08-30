#src/__init__.py
"""
MBTI Quick Test Application
"""

from .config import AppConfig
from .mbti_analyzer import MBTIAnalyzer
from .question_manager import QuestionManager
from .ui_components import UIComponents
from .utils import StateManager, ValidataionUtils, DataUtils, LoggingUtils

__version__ = "2.0.0"
__author__ = "JBS"

__all__ = [
    "AppConfig",
    "MBTIAnalyzer",
    "QuestionManager",
    "UIComponents",
    "StateManager",
    "ValidataionUtils",
    "DataUtils",
    "LoggingUtils",
]

#tests/__init__.py
"""
Test Suite for MBTI Quick Test Application
"""