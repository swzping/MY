from typing import Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import random

class NamingInput(BaseModel):
    surname: str = Field(..., description="Family name (Surname)")
    gender: str = Field(..., description="Gender (boy/girl)")

class NamingTool(BaseTool):
    name: str = "naming_suggestion"
    description: str = "Generate name suggestions based on surname and gender."
    args_schema: type[BaseModel] = NamingInput

    def _run(self, surname: str, gender: str) -> Dict:
        try:
            suggestions = self._generate_names(surname, gender)
            return {
                "surname": surname,
                "gender": gender,
                "suggestions": suggestions
            }
        except Exception as e:
            return {"error": str(e)}

    def _generate_names(self, surname: str, gender: str) -> list:
        # Mock logic
        boy_chars = ["伟", "强", "磊", "洋", "勇", "军", "杰", "涛", "明", "刚"]
        girl_chars = ["芳", "娜", "敏", "静", "秀", "娟", "英", "华", "慧", "巧"]
        
        chars = boy_chars if gender == "boy" else girl_chars
        
        names = []
        for _ in range(5):
            # Generate 2-character given name
            n1 = random.choice(chars)
            n2 = random.choice(chars)
            full_name = f"{surname}{n1}{n2}"
            score = random.randint(80, 100)
            names.append({"name": full_name, "score": score, "meaning": "Good fortune"})
            
        return names

    async def _arun(self, surname: str, gender: str) -> Dict:
        return self._run(surname, gender)
