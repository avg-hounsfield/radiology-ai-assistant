"""
Fallback LLM Manager for cloud deployment when Ollama is not available
Provides basic medical radiology responses without external dependencies
"""

import logging
from typing import Dict, List, Optional
import json
import re

class FallbackLLMManager:
    """Simple fallback LLM that provides basic medical radiology responses"""

    def __init__(self, model_name: str = "fallback"):
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)

        # Basic radiology knowledge base
        self.knowledge_base = {
            "pneumonia": {
                "ct_signs": ["consolidation", "ground-glass opacities", "tree-in-bud pattern", "air bronchograms"],
                "distribution": "lobar, segmental, or patchy bilateral",
                "complications": ["pleural effusion", "cavitation", "ARDS"]
            },
            "pulmonary_edema": {
                "ct_signs": ["ground-glass opacities", "smooth interlobular septal thickening", "crazy paving"],
                "distribution": "bilateral, symmetric, gravitational",
                "causes": ["cardiac", "non-cardiac", "high altitude"]
            },
            "pulmonary_embolism": {
                "ct_signs": ["filling defect", "vessel cutoff", "mosaic attenuation"],
                "distribution": "segmental or subsegmental",
                "complications": ["right heart strain", "pulmonary infarction"]
            },
            "copd": {
                "ct_signs": ["emphysema", "air trapping", "bronchial wall thickening"],
                "distribution": "upper lobe predominant (emphysema)",
                "complications": ["bullae", "pneumothorax", "cor pulmonale"]
            }
        }

        self.logger.info("✅ Fallback LLM manager initialized for cloud deployment")

    def generate_response(self, prompt: str, context: str = "", max_tokens: int = 500) -> str:
        """Generate a basic medical response based on keywords"""

        prompt_lower = prompt.lower()

        # Check for specific medical conditions
        for condition, info in self.knowledge_base.items():
            if condition.replace("_", " ") in prompt_lower or any(sign in prompt_lower for sign in info["ct_signs"]):
                return self._format_medical_response(condition, info, prompt)

        # Generic medical response patterns
        if any(word in prompt_lower for word in ["ct", "chest", "lung", "pulmonary"]):
            return self._generic_chest_response(prompt)
        elif any(word in prompt_lower for word in ["brain", "head", "neurologic"]):
            return self._generic_neuro_response(prompt)
        elif any(word in prompt_lower for word in ["abdomen", "abdominal", "liver", "kidney"]):
            return self._generic_abdomen_response(prompt)
        else:
            return self._generic_response(prompt)

    def _format_medical_response(self, condition: str, info: Dict, original_prompt: str) -> str:
        """Format a structured medical response"""
        condition_name = condition.replace("_", " ").title()

        response = f"## {condition_name}\n\n"
        response += f"**Key CT Findings:**\n"
        for sign in info["ct_signs"]:
            response += f"• {sign.title()}\n"

        response += f"\n**Distribution:** {info['distribution']}\n"

        if "complications" in info:
            response += f"\n**Potential Complications:**\n"
            for comp in info["complications"]:
                response += f"• {comp.title()}\n"

        response += f"\n*Note: This is a basic reference. Please consult current medical literature for comprehensive information.*"

        return response

    def _generic_chest_response(self, prompt: str) -> str:
        """Generic chest imaging response"""
        return """## Chest CT Imaging

Common findings to evaluate:
• **Lung parenchyma**: Look for consolidation, ground-glass, nodules
• **Airways**: Assess for bronchial wall thickening, tree-in-bud
• **Pleura**: Check for effusions, pneumothorax, thickening
• **Mediastinum**: Evaluate lymph nodes, great vessels
• **Bones**: Review for fractures, metastases

*This is a basic reference from the fallback system. For detailed analysis, please use the full system with Ollama.*"""

    def _generic_neuro_response(self, prompt: str) -> str:
        """Generic neuro imaging response"""
        return """## Neuroimaging Basics

Key areas to evaluate:
• **Gray-white matter differentiation**
• **Ventricular system size and symmetry**
• **Midline shift or mass effect**
• **Hemorrhage or ischemic changes**
• **Extra-axial collections**

*This is a basic reference from the fallback system. For detailed analysis, please use the full system with Ollama.*"""

    def _generic_abdomen_response(self, prompt: str) -> str:
        """Generic abdominal imaging response"""
        return """## Abdominal CT Basics

Systematic evaluation:
• **Liver**: Size, density, focal lesions
• **Kidneys**: Size, enhancement, hydronephrosis
• **Pancreas**: Enhancement pattern, ductal dilatation
• **Bowel**: Wall thickness, enhancement, obstruction
• **Vessels**: Aorta, portal vein patency

*This is a basic reference from the fallback system. For detailed analysis, please use the full system with Ollama.*"""

    def _generic_response(self, prompt: str) -> str:
        """Generic fallback response"""
        return """## ECHO Radiology Assistant (Cloud Mode)

This is the fallback response system. The full AI capabilities are not available in the cloud deployment due to infrastructure limitations.

**Available Features:**
• Flashcard study system (13,806+ cards)
• Crack the Core method
• Reference materials
• Study progress tracking

**For full AI-powered responses, please use the local installation with Ollama.**

*You can still access all study materials and flashcards through the Study Mode.*"""

    def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """Chat interface compatible with MedicalLLMManager"""
        if not messages:
            return {"content": "Please provide a question."}

        last_message = messages[-1].get("content", "")
        response = self.generate_response(last_message)

        return {"content": response}

    def is_available(self) -> bool:
        """Check if the LLM is available"""
        return True  # Fallback is always available