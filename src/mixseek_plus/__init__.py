"""mixseek-plus: mixseek-coreの拡張パッケージ."""

from mixseek_plus.agents import (
    ClaudeCodePlainAgent,
    GroqPlainAgent,
    GroqWebSearchAgent,
    register_claudecode_agents,
    register_groq_agents,
)
from mixseek_plus.core_patch import GroqNotPatchedError, check_groq_support, patch_core
from mixseek_plus.errors import ClaudeCodeNotPatchedError, ModelCreationError
from mixseek_plus.model_factory import create_model
from mixseek_plus.providers.claudecode import create_claudecode_model

__all__ = [
    "create_model",
    "create_claudecode_model",
    "ModelCreationError",
    "ClaudeCodeNotPatchedError",
    "GroqPlainAgent",
    "GroqWebSearchAgent",
    "ClaudeCodePlainAgent",
    "register_groq_agents",
    "register_claudecode_agents",
    "patch_core",
    "GroqNotPatchedError",
    "check_groq_support",
]
