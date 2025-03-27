"""
LightYtSearch - A lightweight YouTube search library without API dependencies
"""

from .core import search_youtube
from .extractors import YTInitialDataExtractor

__all__ = ['search_youtube', 'YTInitialDataExtractor']