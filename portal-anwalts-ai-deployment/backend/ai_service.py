"""
Together AI Service Integration
Handles all AI completions using Together API with German legal specialization
"""

import httpx
import json
import time
import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    content: str
    tokens_used: int
    cost_estimate: float
    generation_time_ms: int
    model_used: str
    prompt_used: Optional[str] = None

@dataclass 
class DocumentGenerationResponse:
    content: str
    prompt_used: str
    tokens_used: int
    cost_estimate: float
    generation_time_ms: int
    model_used: str

class AIService:
    """Service for handling AI completions via Together API"""
    
    def __init__(self):
        self.api_key = os.getenv("TOGETHER_API_KEY")
        self.base_url = "https://api.together.xyz/v1"
        self.default_model = os.getenv("DEFAULT_AI_MODEL", "deepseek-ai/DeepSeek-V3")
        
        # Model pricing per 1M tokens (approximate)
        self.model_pricing = {
            "deepseek-ai/DeepSeek-V3": {"input": 0.27, "output": 1.10},
            "meta-llama/Llama-3.1-70B-Instruct-Turbo": {"input": 0.88, "output": 0.88},
            "meta-llama/Llama-3.1-8B-Instruct-Turbo": {"input": 0.18, "output": 0.18},
            "mixtral-8x7b-instruct-v0.1": {"input": 0.6, "output": 0.6},
            "mistralai/Mixtral-8x22B-Instruct-v0.1": {"input": 1.2, "output": 1.2}
        }
        
        # German legal system prompts
        self.system_prompts = {
            "legal_document": """Sie sind ein erfahrener deutscher Rechtsanwalt mit Spezialisierung auf die Erstellung präziser Rechtsdokumente. 
            Ihre Aufgabe ist es, rechtlich korrekte, vollständige und praxistaugliche Dokumente zu erstellen, die den deutschen Rechtssystem entsprechen.
            
            Wichtige Prinzipien:
            - Verwenden Sie präzise deutsche Rechtssprache
            - Berücksichtigen Sie aktuelle deutsche Gesetze (BGB, ZPO, etc.)
            - Strukturieren Sie Dokumente logisch und übersichtlich
            - Fügen Sie relevante Rechtsgrundlagen hinzu
            - Achten Sie auf DSGVO-Konformität bei personenbezogenen Daten""",
            
            "contract": """Sie sind ein Experte für deutsches Vertragsrecht. Erstellen Sie rechtssichere Verträge, die:
            - Den Anforderungen des BGB entsprechen
            - Alle wesentlichen Vertragsbestandteile enthalten
            - Klar strukturiert und verständlich sind
            - Risiken minimieren und Rechte schützen
            - Bei Bedarf Schlichtungsklauseln enthalten""",
            
            "email": """Sie sind ein professioneller deutscher Rechtsanwalt. Verfassen Sie höfliche, präzise und rechtlich fundierte E-Mails, die:
            - Einen professionellen Ton wahren
            - Rechtliche Sachverhalte klar erläutern
            - Handlungsempfehlungen geben
            - Bei Bedarf auf Fristen hinweisen
            - Mandantenbeziehungen stärken""",
            
            "clause": """Sie sind ein Spezialist für deutsche Vertragsklauseln. Erstellen Sie rechtssichere Klauseln, die:
            - Rechtlich bindend und durchsetzbar sind
            - Eindeutig formuliert sind
            - Deutsche Rechtsprechung berücksichtigen
            - Praktisch anwendbar sind
            - Bei Bedarf Alternative Streitbeilegung vorsehen"""
        }
    
    async def generate_completion(
        self,
        prompt: str,
        model: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        context: str = "general"
    ) -> AIResponse:
        """Generate AI completion using Together API"""
        start_time = time.time()
        
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY environment variable is required")
        
        model = model or self.default_model
        system_prompt = self.system_prompts.get(context, self.system_prompts["legal_document"])
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract response data
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                
                # Calculate cost estimate
                cost_estimate = self._calculate_cost(model, tokens_used)
                generation_time_ms = int((time.time() - start_time) * 1000)
                
                logger.info(f"AI completion successful: {tokens_used} tokens, {generation_time_ms}ms")
                
                return AIResponse(
                    content=content,
                    tokens_used=tokens_used,
                    cost_estimate=cost_estimate,
                    generation_time_ms=generation_time_ms,
                    model_used=model
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Together API HTTP error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code} - {e.response.text}")
                raise Exception(f"AI service error: {e.response.status_code}")
            else:
                raise Exception(f"AI service HTTP error: {str(e)}")
        except httpx.TimeoutException:
            logger.error("Together API timeout")
            raise Exception("AI service timeout")
        except Exception as e:
            logger.error(f"AI completion error: {e}")
            raise Exception(f"AI completion failed: {str(e)}")
    
    async def generate_document(
        self,
        document_type: str,
        template_content: str = "",
        variables: Dict[str, Any] = None,
        model: str = None
    ) -> DocumentGenerationResponse:
        """Generate complete legal document"""
        start_time = time.time()
        
        variables = variables or {}
        model = model or self.default_model
        
        # Build comprehensive prompt for document generation
        prompt = self._build_document_prompt(document_type, template_content, variables)
        
        # Select appropriate system prompt based on document type
        context = self._get_context_for_document_type(document_type)
        
        try:
            response = await self.generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=4000,
                temperature=0.2,
                context=context
            )
            
            return DocumentGenerationResponse(
                content=response.content,
                prompt_used=prompt,
                tokens_used=response.tokens_used,
                cost_estimate=response.cost_estimate,
                generation_time_ms=response.generation_time_ms,
                model_used=response.model_used
            )
            
        except Exception as e:
            logger.error(f"Document generation error: {e}")
            raise Exception(f"Document generation failed: {str(e)}")
    
    async def generate_email_response(
        self,
        original_email: str,
        response_type: str = "professional",
        key_points: List[str] = None,
        model: str = None
    ) -> AIResponse:
        """Generate professional legal email response"""
        key_points = key_points or []
        
        prompt = f"""
        Verfassen Sie eine professionelle Antwort auf die folgende E-Mail:

        URSPRÜNGLICHE E-MAIL:
        {original_email}

        ANTWORTTYP: {response_type}

        WICHTIGE PUNKTE ZU BERÜCKSICHTIGEN:
        {chr(10).join([f'- {point}' for point in key_points])}

        Bitte erstellen Sie eine höfliche, professionelle und rechtlich fundierte Antwort, die:
        1. Alle wichtigen Punkte anspricht
        2. Bei Bedarf rechtliche Hinweise gibt
        3. Nächste Schritte klar definiert
        4. Einen angemessenen professionellen Ton verwendet
        """
        
        return await self.generate_completion(
            prompt=prompt,
            model=model,
            context="email"
        )
    
    async def generate_clause(
        self,
        clause_type: str,
        purpose: str,
        specific_requirements: List[str] = None,
        model: str = None
    ) -> AIResponse:
        """Generate specific legal clause"""
        specific_requirements = specific_requirements or []
        
        prompt = f"""
        Erstellen Sie eine rechtssichere deutsche Vertragsklausel:

        KLAUSELTYP: {clause_type}
        ZWECK: {purpose}

        SPEZIFISCHE ANFORDERUNGEN:
        {chr(10).join([f'- {req}' for req in specific_requirements])}

        Die Klausel soll:
        1. Rechtlich bindend und durchsetzbar sein
        2. Eindeutig und unmissverständlich formuliert sein
        3. Deutsche Rechtsprechung berücksichtigen
        4. Praktisch anwendbar sein
        5. Beide Vertragsparteien fair behandeln

        Fügen Sie bitte eine kurze Erläuterung zur rechtlichen Bedeutung hinzu.
        """
        
        return await self.generate_completion(
            prompt=prompt,
            model=model,
            context="clause"
        )
    
    def _build_document_prompt(
        self,
        document_type: str,
        template_content: str,
        variables: Dict[str, Any]
    ) -> str:
        """Build comprehensive prompt for document generation"""
        
        prompt = f"""
        Erstellen Sie ein vollständiges deutsches Rechtsdokument:

        DOKUMENTTYP: {document_type}
        """
        
        if template_content:
            prompt += f"""
        
        VORLAGE/GRUNDLAGE:
        {template_content}
        """
        
        if variables:
            prompt += """
        
        VARIABLE/DATEN ZU BERÜCKSICHTIGEN:
        """
            for key, value in variables.items():
                prompt += f"- {key}: {value}\n"
        
        prompt += f"""
        
        ANFORDERUNGEN:
        1. Verwenden Sie korrektes deutsches Recht und Rechtssprache
        2. Strukturieren Sie das Dokument logisch und übersichtlich
        3. Fügen Sie alle notwendigen rechtlichen Klauseln hinzu
        4. Berücksichtigen Sie aktuelle Gesetze und Rechtsprechung
        5. Stellen Sie sicher, dass das Dokument rechtlich bindend ist
        6. Verwenden Sie professionelle Formatierung
        7. Fügen Sie Datum und Unterschriftenfelder hinzu
        
        Erstellen Sie ein vollständiges, anwendungsbereites Dokument.
        """
        
        return prompt
    
    def _get_context_for_document_type(self, document_type: str) -> str:
        """Get appropriate context/system prompt for document type"""
        document_type_lower = document_type.lower()
        
        if any(term in document_type_lower for term in ["vertrag", "contract", "vereinbarung"]):
            return "contract"
        elif any(term in document_type_lower for term in ["email", "brief", "anschreiben"]):
            return "email"
        elif any(term in document_type_lower for term in ["klausel", "clause", "bedingung"]):
            return "clause"
        else:
            return "legal_document"
    
    def _calculate_cost(self, model: str, tokens_used: int) -> float:
        """Calculate estimated cost for API usage"""
        pricing = self.model_pricing.get(model, {"input": 1.0, "output": 1.0})
        
        # Estimate input/output split (rough approximation)
        input_tokens = int(tokens_used * 0.3)
        output_tokens = int(tokens_used * 0.7)
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Together AI models"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                
                data = response.json()
                models = []
                
                for model in data.get("data", []):
                    if model.get("object") == "model":
                        models.append({
                            "id": model.get("id"),
                            "name": model.get("display_name", model.get("id")),
                            "context_length": model.get("context_length", 4096),
                            "pricing": self.model_pricing.get(model.get("id"), {"input": 0, "output": 0})
                        })
                
                return models
                
        except Exception as e:
            logger.error(f"Failed to fetch available models: {e}")
            return [
                {
                    "id": self.default_model,
                    "name": "Llama 3.1 70B (Default)",
                    "context_length": 8192,
                    "pricing": self.model_pricing[self.default_model]
                }
            ]
    
    def health_check(self) -> bool:
        """Check if AI service is healthy"""
        return bool(self.api_key)