# utils/helpers.py
import json
import time
from typing import Any, Dict
from colorama import Fore, Style
from datetime import datetime

def format_price(price: float, currency: str = 'USD') -> str:
    """Форматирует цену с разделителями"""
    if price is None:
        return 'N/A'
    
    if currency == 'USD' or currency == 'USDT':
        return f"${price:,.2f}"
    else:
        return f"{price:,.8f}"

def format_percentage(value: float) -> str:
    """Форматирует процентное значение"""
    if value is None:
        return 'N/A'
    
    color = Fore.GREEN if value >= 0 else Fore.RED
    return f"{color}{value:+.2f}%{Style.RESET_ALL}"

def calculate_sma(data: list, period: int) -> float:
    """Рассчитывает простую скользящую среднюю"""
    if len(data) < period:
        return None
    return sum(data[-period:]) / period

def save_to_json(data: Any, filename: str):
    """Сохраняет данные в JSON файл"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"{Fore.GREEN}✅ Данные сохранены в {filename}")

def load_from_json(filename: str) -> Any:
    """Загружает данные из JSON файла"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.YELLOW}⚠️ Файл {filename} не найден")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ Ошибка загрузки {filename}: {e}")
        return None

class Timer:
    """Таймер для измерения производительности"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
        print(f"{Fore.CYAN}⏱️ {self.name} занял {self.interval:.3f} секунд")