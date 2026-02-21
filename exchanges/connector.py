# exchanges/connector.py
import ccxt
from typing import Dict, List, Optional
import time
from colorama import Fore, Style, init

init(autoreset=True)

class ExchangeConnector:
    """Базовый класс для подключения к биржам"""
    
    def __init__(self, exchange_id: str, config: dict = None):
        self.exchange_id = exchange_id
        self.config = config or {}
        self.exchange = self._create_exchange()
        
    def _create_exchange(self):
        """Создает подключение к бирже"""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,
                'timeout': 30000,
                **self.config
            })
            return exchange
        except AttributeError:
            raise ValueError(f"Биржа {self.exchange_id} не поддерживается")
    
    def get_ticker(self, symbol: str) -> Dict:
        """Получает тикер для пары"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'high': ticker['high'],
                'low': ticker['low'],
                'change': ticker['percentage'],
                'timestamp': ticker['timestamp'] or int(time.time() * 1000)
            }
        except Exception as e:
            print(f"{Fore.RED}Ошибка получения тикера {symbol}: {e}")
            return None
    
    def get_order_book(self, symbol: str, limit: int = 10) -> Dict:
        """Получает стакан ордеров"""
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return {
                'bids': order_book['bids'][:limit],
                'asks': order_book['asks'][:limit],
                'timestamp': order_book['timestamp']
            }
        except Exception as e:
            print(f"{Fore.RED}Ошибка получения стакана {symbol}: {e}")
            return None
    
    def get_balance(self) -> Dict:
        """Получает баланс (требуются API ключи)"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total': balance['total'],
                'free': balance['free'],
                'used': balance['used']
            }
        except Exception as e:
            print(f"{Fore.RED}Ошибка получения баланса: {e}")
            return None
    
    def get_multiple_tickers(self, symbols: List[str]) -> Dict[str, Dict]:
        """Получает тикеры для нескольких пар"""
        results = {}
        for symbol in symbols:
            ticker = self.get_ticker(symbol)
            if ticker:
                results[symbol] = ticker
            time.sleep(self.exchange.rateLimit / 1000)  # Соблюдаем лимиты
        return results
    
    def calculate_spread(self, symbol: str) -> Optional[float]:
        """Вычисляет спред в процентах"""
        ticker = self.get_ticker(symbol)
        if ticker and ticker['ask'] and ticker['bid']:
            spread = (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100
            return spread
        return None
    
    def print_portfolio(self):
        """Заглушка для совместимости с PaperExchange"""
        balance = self.get_balance()
        if balance:
            print(f"\n{Fore.CYAN}{'='*50}")
            print(f"📊 ПОРТФЕЛЬ (Реальный)")
            print(f"{'='*50}")
            
            total = 0
            for currency, amount in balance['total'].items():
                if amount > 0:
                    try:
                        ticker = self.get_ticker(f"{currency}/USDT")
                        if ticker and ticker.get('last'):
                            usd_value = amount * ticker['last']
                            total += usd_value
                            print(f"{currency}: {amount:.8f} ≈ ${usd_value:.2f}")
                        else:
                            print(f"{currency}: {amount}")
                    except:
                        print(f"{currency}: {amount}")
            
            print(f"{Fore.GREEN}💰 ОБЩАЯ СТОИМОСТЬ: ~${total:.2f}")
            print(f"{Fore.CYAN}{'='*50}\n")