import json
from typing import Protocol
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

class ReviewerProvider(Protocol):
    async def review(self, system_prompt: str, evidence_bundle: str) -> dict:
        """
        Takes the system prompt and the evidence bundle, returns a parsed JSON dict.
        Must raise an exception if the LLM fails or returns invalid JSON.
        """
        ...

class VertexProvider:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # Initialize Vertex AI globally if not already done
        import os
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project_id:
            vertexai.init(project=project_id)
        else:
            vertexai.init()
        self.model_name = model_name

    async def review(self, system_prompt: str, evidence_bundle: str) -> dict:
        # Defer GenerativeModel initialization so import doesn't fail without ADC
        model = GenerativeModel(self.model_name, system_instruction=system_prompt)
        
        response = model.generate_content(
            contents=evidence_bundle,
            generation_config=GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
