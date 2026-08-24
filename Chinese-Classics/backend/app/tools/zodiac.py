from typing import Dict, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class ZodiacInput(BaseModel):
    year: int = Field(..., description="Birth year (e.g., 1990)")

class ZodiacTool(BaseTool):
    name: str = "zodiac_calculator"
    description: str = "Calculate Chinese Zodiac sign and compatibility based on birth year."
    args_schema: type[BaseModel] = ZodiacInput

    def _run(self, year: int) -> Dict:
        try:
            sign = self._get_zodiac_sign(year)
            compatibility = self._get_compatibility(sign)
            return {
                "year": year,
                "sign": sign,
                "compatibility": compatibility
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_zodiac_sign(self, year: int) -> str:
        zodiacs = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
        # 1900 is Rat (鼠)
        # (year - 1900) % 12
        # Actually 1900 is Rat.
        # But wait, usually standard is (year - 4) % 12 for standard sequence starting with Rat at index 0?
        # Let's check: 2024 is Dragon.
        # (2024 - 1900) % 12 = 124 % 12 = 4. 
        # Index 0=Rat, 1=Ox, 2=Tiger, 3=Rabbit, 4=Dragon. Correct.
        start_year = 1900
        index = (year - start_year) % 12
        return zodiacs[index]

    def _get_compatibility(self, sign: str) -> Dict[str, List[str]]:
        # Simplified compatibility table
        compatibility_map = {
            "鼠": {"best": ["龙", "猴", "牛"], "worst": ["马", "羊", "鸡"]},
            "牛": {"best": ["鼠", "蛇", "鸡"], "worst": ["马", "羊", "狗"]},
            "虎": {"best": ["马", "狗", "猪"], "worst": ["蛇", "猴"]},
            "兔": {"best": ["羊", "狗", "猪"], "worst": ["鼠", "鸡", "龙"]},
            "龙": {"best": ["鼠", "猴", "鸡"], "worst": ["狗", "兔"]},
            "蛇": {"best": ["牛", "鸡"], "worst": ["猪", "虎"]},
            "马": {"best": ["虎", "羊", "狗"], "worst": ["鼠", "牛"]},
            "羊": {"best": ["兔", "马", "猪"], "worst": ["鼠", "牛", "狗"]},
            "猴": {"best": ["鼠", "龙"], "worst": ["虎", "猪"]},
            "鸡": {"best": ["牛", "龙", "蛇"], "worst": ["兔", "狗"]},
            "狗": {"best": ["虎", "兔", "马"], "worst": ["牛", "龙", "羊"]},
            "猪": {"best": ["羊", "兔", "虎"], "worst": ["蛇", "猴", "猪"]}
        }
        return compatibility_map.get(sign, {"best": [], "worst": []})

    async def _arun(self, year: int) -> Dict:
        return self._run(year)
