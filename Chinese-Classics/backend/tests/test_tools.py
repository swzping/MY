import pytest
import sys
import os

# Add project root to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.tools.iching import IChingTool
from app.tools.horoscope import HoroscopeTool
from app.tools.bazi import BaZiTool
from app.tools.zodiac import ZodiacTool
from app.tools.naming import NamingTool

def test_iching_tool():
    tool = IChingTool()
    result = tool._run("Will I pass the exam?")
    assert "lines" in result
    assert len(result["lines"]) == 6
    assert "original_hexagram" in result

def test_horoscope_tool():
    tool = HoroscopeTool()
    # Test Aries
    result = tool._run("2023-03-25")
    assert result["sign"] == "白羊座"
    
    # Test Capricorn (cross year/month boundary)
    result = tool._run("2023-01-01")
    assert result["sign"] == "摩羯座"
    
    # Test Invalid Date
    result = tool._run("invalid-date")
    assert "error" in result

def test_bazi_tool():
    tool = BaZiTool()
    result = tool._run("1990-01-01 12:00")
    assert "year_pillar" in result
    assert result["year_pillar"] == "甲子"  # Mock result

def test_zodiac_tool():
    tool = ZodiacTool()
    # Test Dragon
    result = tool._run(2024)
    assert result["sign"] == "龙"
    assert "compatibility" in result
    assert "best" in result["compatibility"]
    
    # Test Rat
    result = tool._run(1900)
    assert result["sign"] == "鼠"

def test_naming_tool():
    tool = NamingTool()
    result = tool._run("李", "boy")
    assert "suggestions" in result
    assert len(result["suggestions"]) == 5
    assert result["suggestions"][0]["name"].startswith("李")
