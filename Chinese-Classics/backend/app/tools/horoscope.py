from typing import Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
import json

class HoroscopeInput(BaseModel):
    date_str: str = Field(..., description="Birth date in YYYY-MM-DD format")

class HoroscopeTool(BaseTool):
    name: str = "horoscope_calculator"
    description: str = "Calculate horoscope sign based on birth date."
    args_schema: type[BaseModel] = HoroscopeInput

    def _run(self, date_str: str) -> Dict:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            month = dt.month
            day = dt.day
            sign = self._get_sign(month, day)
            return {"sign": sign, "date": date_str}
        except ValueError:
            return {"error": "Invalid date format. Please use YYYY-MM-DD."}
        except Exception as e:
            return {"error": str(e)}

    def _get_sign(self, month: int, day: int) -> str:
        dates = [20, 19, 21, 20, 21, 22, 23, 23, 23, 24, 22, 22]
        signs = [
            "摩羯座", "水瓶座", "双鱼座", "白羊座", "金牛座", "双子座",
            "巨蟹座", "狮子座", "处女座", "天秤座", "天蝎座", "射手座", "摩羯座"
        ]
        if day > dates[month - 1]:
            return signs[month]
        else:
            return signs[month - 1]

    async def _arun(self, date_str: str) -> Dict:
        return self._run(date_str)
