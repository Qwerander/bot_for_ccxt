# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки бирж
EXCHANGES = {
    'primary': 'bybit',
    'secondary': ['binance', 'kucoin', 'okx']
}

# Настройки paper trading
PAPER_TRADING = {
    'initial_balance': 10000,  # Начальный баланс в USDT
    'fee_percentage': 0.1,      # Комиссия 0.1%
    'slippage': 0.05,           # Проскальзывание 0.05%
}

# Торговые пары
TRADING_PAIRS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

# Пороги для уведомлений
ALERT_THRESHOLDS = {
    'btc_upper': 70000,
    'btc_lower': 60000,
    'eth_upper': 4000,
    'eth_lower': 3000,
    'arbitrage_percent': 0.5,   # Минимальная разница для арбитража
}

# API ключи (будут загружены из .env файла)
API_KEYS = {
    'bybit': {
        'apiKey': os.getenv('BYBIT_API_KEY', ''),
        'secret': os.getenv('BYBIT_SECRET', '')
    },
    'binance': {
        'apiKey': os.getenv('BINANCE_API_KEY', ''),
        'secret': os.getenv('BINANCE_SECRET', '')
    }
}

# Настройки рисков для реальной торговли
RISK_MANAGEMENT = {
    'max_trade_size_usdt': 100,  # Максимальный размер сделки в USDT
    'max_daily_loss_usdt': 500,   # Максимальный дневной убыток
    'max_open_positions': 3,       # Максимум открытых позиций
    'stop_loss_percent': 5,        # Стоп-лосс по умолчанию
    'take_profit_percent': 10,     # Тейк-профит по умолчанию
}

# Режим торговли (можно менять здесь или через аргументы командной строки)
TRADING_MODE = os.getenv('TRADING_MODE', 'paper')  # 'paper' или 'real'
DEFAULT_EXCHANGE = os.getenv('DEFAULT_EXCHANGE', 'binance')