import logging
from typing import Any, Dict, Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class ProviderError(Exception):
    pass

class ProviderTimeoutError(ProviderError):
    pass

class BaseProvider:
    async def generate_structured(self, prompt: str, schema: Type[T], max_retries: int = 1) -> T:
        raise NotImplementedError()

class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ProviderError("Missing Google API Key")
        self.api_key = api_key
        self.model = model
        import google.genai as genai
        self.client = genai.Client(api_key=api_key)

    async def generate_structured(self, prompt: str, schema: Type[T], max_retries: int = 1) -> T:
        from google.genai import types
        attempts = 0
        while attempts <= max_retries:
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )
                if not response.text:
                    raise ProviderError("Empty response from LLM")
                return schema.model_validate_json(response.text)
            except ValidationError as e:
                attempts += 1
                if attempts > max_retries:
                    raise ProviderError("Failed to parse LLM structured output") from e
            except Exception as e:
                attempts += 1
                if attempts > max_retries:
                    logger.error(f"LLM generation failed after {attempts} attempts: {e}")
                    raise ProviderError("Fail-closed: LLM generation failed") from e

class FakeProvider(BaseProvider):
    """Deterministic fake provider for unit tests and CI."""
    def __init__(self, responses: Optional[Dict[str, Any]] = None, timeout: bool = False, malformed: bool = False):
        self.responses = responses or {}
        self.timeout = timeout
        self.malformed = malformed

    async def generate_structured(self, prompt: str, schema: Type[T], max_retries: int = 1) -> T:
        if self.timeout:
            raise ProviderTimeoutError("Simulated timeout")
        
        if self.malformed:
            if max_retries > 0:
                # Simulate a repair on the second try
                self.malformed = False
            else:
                raise ProviderError("Simulated malformed output could not be parsed")
            
        # Return a deterministic response based on the schema name or prompt
        schema_name = schema.__name__
        if schema_name in self.responses:
            try:
                return schema(**self.responses[schema_name])
            except ValidationError as e:
                raise ProviderError("Fake response does not match schema") from e
        
        # Fallback empty object
        return schema.model_construct()
