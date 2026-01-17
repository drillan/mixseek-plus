"""Groq API統合テスト.

実際のGroq APIを使用してモデル作成と基本的なAPI呼び出しをテストする.
環境変数 GROQ_API_KEY が設定されている場合のみ実行される.
"""

import os

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

from mixseek_plus import create_model


@pytest.mark.integration
class TestGroqApiIntegration:
    """Groq API統合テスト."""

    @pytest.fixture(autouse=True)
    def check_groq_api_key(self) -> None:
        """GROQ_API_KEYが設定されていない場合はテストをスキップする."""
        if not os.getenv("GROQ_API_KEY"):
            pytest.skip("GROQ_API_KEY not set")

    def test_create_model_returns_groq_model(self) -> None:
        """create_modelがGroqModelインスタンスを返すことを確認."""
        model = create_model("groq:llama-3.3-70b-versatile")

        assert isinstance(model, GroqModel)

    @pytest.mark.asyncio
    async def test_groq_model_can_generate_response(self) -> None:
        """GroqモデルがAPIを通じてレスポンスを生成できることを確認."""
        model = create_model("groq:llama-3.1-8b-instant")
        agent = Agent(model)

        result = await agent.run("Reply with just 'hello' in lowercase.")

        assert result.output is not None
        assert "hello" in result.output.lower()
