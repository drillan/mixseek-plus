"""プロバイダー定数とユーティリティ."""

# Groqプロバイダーの識別子
GROQ_PROVIDER_PREFIX: str = "groq:"

# mixseek-coreでサポートされているプロバイダープレフィックス一覧
CORE_PROVIDER_PREFIXES: frozenset[str] = frozenset(
    {
        "google-gla:",
        "google-vertex:",
        "openai:",
        "anthropic:",
        "grok:",
        "grok-responses:",
    }
)

# 全サポートプロバイダープレフィックス（mixseek-plus + mixseek-core）
ALL_PROVIDER_PREFIXES: frozenset[str] = CORE_PROVIDER_PREFIXES | {GROQ_PROVIDER_PREFIX}
