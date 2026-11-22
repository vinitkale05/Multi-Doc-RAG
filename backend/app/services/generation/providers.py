import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass

    @abstractmethod
    async def stream_generate(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        pass


class LocalMockLLMProvider(BaseLLMProvider):
    """Grounded mock LLM that extracts facts from context blocks [S1], [S2]

    and synthesizes verifiable citations. Ideal for testing, evaluation harnesses, and fallback.
    """

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if "<context>\n\n</context>" in user_prompt or "<context>\n</context>" in user_prompt:
            return "Based on the provided documents, there is insufficient evidence to answer this question."

        blocks = re.findall(r"\[(S\d+)\][^\n]*\n(.*?)(?=\n\n---\n\n|\n</context>)", user_prompt, re.DOTALL)
        if not blocks:
            return "Based on the provided documents, there is insufficient evidence to answer this question."

        answer_parts = []
        for sid, text in blocks[:3]:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s.strip()) > 20]
            if sentences:
                picked = sentences[0]
                if not picked.startswith("#") and "NEUTRALIZED" not in picked:
                    cleaned_sent = picked.rstrip(".")
                    answer_parts.append(f"{cleaned_sent} [{sid}].")

        if not answer_parts:
            return "Based on the provided documents, there is insufficient evidence to answer this question."

        full_answer = " ".join(answer_parts)
        return full_answer

    async def stream_generate(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        full_text = await self.generate(system_prompt, user_prompt)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.015)


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str = settings.LLM_API_KEY, model: str = settings.LLM_MODEL or "gemini-flash-latest"):
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            return await LocalMockLLMProvider().generate(system_prompt, user_prompt)

        models_to_try = [self.model, "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-002"]
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": settings.LLM_TEMPERATURE,
                "maxOutputTokens": settings.LLM_MAX_TOKENS
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            last_err = None
            for m in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return text
                    elif resp.status_code in [429, 503]:
                        logger.warning(f"Gemini model {m} returned {resp.status_code}, trying next model or retry...")
                        await asyncio.sleep(1.0)
                        continue
                    else:
                        logger.error(f"Gemini API returned error {resp.status_code}: {resp.text}")
                        last_err = resp.text
                except Exception as e:
                    logger.warning(f"Gemini API call to {m} failed: {e}")
                    last_err = str(e)

            logger.error(f"All Gemini models exhausted. Falling back to grounded mock. Last error: {last_err}")
            return await LocalMockLLMProvider().generate(system_prompt, user_prompt)

    async def stream_generate(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        res = await self.generate(system_prompt, user_prompt)
        words = res.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.015)


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str = settings.LLM_API_KEY, model: str = settings.LLM_MODEL):
        self.api_key = api_key
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            return await LocalMockLLMProvider().generate(system_prompt, user_prompt)

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def stream_generate(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        if not self.api_key:
            async for token in LocalMockLLMProvider().stream_generate(system_prompt, user_prompt):
                yield token
            return

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "stream": True,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk_data = json.loads(line[6:])
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue


def get_llm_provider() -> BaseLLMProvider:
    if settings.LLM_PROVIDER == "gemini" and settings.LLM_API_KEY:
        return GeminiLLMProvider()
    elif settings.LLM_PROVIDER == "openai" and settings.LLM_API_KEY:
        return OpenAILLMProvider()
    return LocalMockLLMProvider()
