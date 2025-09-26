from openai import OpenAI
import os

class StreamLLM:
    def __init__(self, provider: str, api_key: str, model: str):
        """
        provider: "openai" | "kimi" | "qwen"
        """
        base_url_map = {
            "openai": "https://api.openai.com/v1",
            "kimi": "https://api.moonshot.cn/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }
        self.client = OpenAI(api_key=api_key, base_url=base_url_map[provider])
        self.model = model

    def stream(self, messages):
        """yield 每一段 token"""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.8,
            max_tokens=4096
        )
        for chunk in resp:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta