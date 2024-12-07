import os
import re
import requests
import json
from typing import Any, Dict

from .constants import END_CODE_TAG, START_CODE_TAG


class LLM:
    """LLM class for generating code from a prompt.

    Args:
        model_name (str, optional): Model name. Defaults to "claude-3-5-sonnet-20240620".
        temperature (int, optional): Temperature. Defaults to 0.2.
        max_tokens (int, optional): Max tokens. Defaults to 1000.
        top_p (int, optional): Top p. Defaults to 1.
        frequency_penalty (int, optional): Frequency penalty. Defaults to 0.
        presence_penalty (int, optional): Presence penalty. Defaults to 0.
        api_key (str, optional): Claude API key. Defaults to None.

    Raises:
        ValueError: If no API key is provided.

    Returns:
        str: Generated code
    """

    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: int = 0.2,
        max_tokens: int = 1000,
        top_p: int = 1,
        frequency_penalty: int = 0,
        presence_penalty: int = 0,
        chat: bool = True,
        api_key: str = None,
    ):
        self.base_url = "https://api.claude-plus.top"
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.chat = chat

        self.api_key = "sk-UjwYbOFayTYngtr69OKAP86ErtGrSdNlOaTV8g4529GMbHry"
        if self.api_key is None:
            raise ValueError("Please provide a Claude API key")

        self.messages = []

    def _extract_code(self, response: str, separator: str = "```") -> str:
        """
        Extract the code from the response.

        Args:
            response (str): Response
            separator (str, optional): Separator. Defaults to "```".

        Returns:
            str: Extracted code from the response
        """
        code = response
        match = re.search(
            rf"{START_CODE_TAG}(.*)({END_CODE_TAG}|{END_CODE_TAG.replace('<', '</')})",
            code,
            re.DOTALL,
        )
        if match:
            code = match.group(1).strip()
        if len(code.split(separator)) > 1:
            code = code.split(separator)[1]

        if self.chat:
            code = code.replace("python", "")

        if "fig.show()" in code:
            code = code.replace("fig.show()", "fig")

        return code

    def generate_code(self, instructions: str) -> str:
        """
        Generate the code based on the instruction and the given prompt.

        Returns:
            str: Code
        """
        if self.chat:
            return self._extract_code(self.chat_completion(instructions))
        else:
            return self._extract_code(self.completion(instructions))

    @property
    def _default_params(self) -> Dict[str, Any]:
        """
        Get the default parameters for calling Claude API

        Returns (Dict): A dict of Claude API parameters

        """

        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }

    def completion(self, prompt: str) -> str:
        """
        Query the completion API

        Args:
            prompt (str): Prompt

        Returns:
            str: LLM response
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = json.dumps({
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        })
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        message = data["choices"][0]["text"]

        return message

    def chat_completion(self, value: str) -> str:
        """
        Query the chat completion API

        Args:
            value (str): Prompt

        Returns:
            str: LLM response
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = json.dumps({
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": value
                }
            ]
        })
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        
        # Debug the response
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {data}")
            
        if "choices" not in data:
            raise Exception(f"Unexpected API response format. Response data: {data}")
            
        message = data["choices"][0]["message"]["content"]

        self.add_history(value, message)
        return message

    def add_history(self, user_message, bot_message):
        self.messages.append({"role": "system", "content": bot_message})
        self.messages.append({"role": "human", "content": user_message})
        return None
