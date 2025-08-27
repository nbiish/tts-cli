"""
Testing framework for TTS models.

This package contains testing utilities, performance benchmarking,
and platform detection for our testing-first approach.
"""

from .model_tester import ModelTester
from .performance_benchmark import PerformanceBenchmark
from .platform_detector import PlatformDetector

__all__ = [
    'ModelTester',
    'PerformanceBenchmark',
    'PlatformDetector'
]
