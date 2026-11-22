"""
Ollama API client.

Sends prompts to a locally running Ollama model and returns the
plain-text response content.

Supports an optional system_prompt so callers can supply a custom
system message per request (used by CommentsAnalyzer).
"""

import requests


class OllamaClient:
    def __init__(
        self,
        model: str = "llama3.2:1b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.api_url = f"{base_url}/api/chat"

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        format: str | None = None,
    ) -> str:
        """
        Generate a response from the Ollama model.

        Parameters
        ----------
        prompt : str
            The user message / prompt text.
        system_prompt : str | None
            Optional system message. When provided it overrides any system
            prompt baked into the Modelfile for this request.
        format : str | None
            Optional Ollama format hint (e.g. "json").

        Returns
        -------
        str
            The model's reply text.

        Raises
        ------
        RuntimeError
            When the Ollama API request fails.
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        if format:
            payload["format"] = format

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=180,
            )
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Ollama API request failed: {error}"
            ) from error
