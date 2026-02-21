# monitors/arbitrage.py
from typing import Dict, List, Tuple
from colorama import Fore, Style
from exchanges.connector import ExchangeConnector
import time

class ArbitrageScanner:
    """Поиск арбитражных возможностей между биржами"""
    
    def __init__(self, exchanges: List[str], min_spread: float = 0.5):
        """
        exchanges: список ID бирж для сканирования
        min_spread: минимальный спред в процентах для сигнала
        """
        self.exchanges = []
        for exchange_id in exchanges:
            try:
                self.exchanges.append(ExchangeConnector(exchange_id))
                print(f"{Fore.GREEN}✅ Подключено к {exchange_id}")
            except Exception as e:
                print(f"{Fore.RED}❌ Ошибка подключения к {exchange_id}: {e}")
        
        self.min_spread = min_spread
        
    def scan_pair(self, symbol: str) -> List[Dict]:
        """
        Сканирует пару на всех биржах и ищет арбитраж
        """
        prices = {}
        
        # Собираем цены со всех бирж
        for exchange in self.exchanges:
            try:
                ticker = exchange.get_ticker(symbol)
                if ticker:
                    prices[exchange.exchange_id] = {
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'last': ticker['last']
                    }
            except Exception as e:
                print(f"{Fore.RED}Ошибка получения данных с {exchange.exchange_id}: {e}")
            
            time.sleep(0.5)  # Пауза между запросами
        
        if len(prices) < 2:
            return []
        
        # Ищем лучшую цену покупки (самый низкий ask)
        best_ask_exchange = min(prices.items(), key=lambda x: x[1]['ask'])
        # Ищем лучшую цену продажи (самый высокий bid)
        best_bid_exchange = max(prices.items(), key=lambda x: x[1]['bid'])
        
        opportunities = []
        
        # Проверяем прямой арбитраж
        if best_bid_exchange[0] != best_ask_exchange[0]:
            spread_percent = (best_bid_exchange[1]['bid'] - best_ask_exchange[1]['ask']) / best_ask_exchange[1]['ask'] * 100
            
            if spread_percent > self.min_spread:
                opportunities.append({
                    'type': 'direct',
                    'buy_exchange': best_ask_exchange[0],
                    'buy_price': best_ask_exchange[1]['ask'],
                    'sell_exchange': best_bid_exchange[0],
                    'sell_price': best_bid_exchange[1]['bid'],
                    'spread_percent': spread_percent,
                    'profit_per_unit': best_bid_exchange[1]['bid'] - best_ask_exchange[1]['ask']
                })
        
        return opportunities
    
    def scan_all_pairs(self, symbols: List[str]) -> Dict[str, List]:
        """
        Сканирует несколько торговых пар
        """
        results = {}
        
        for symbol in symbols:
            opportunities = self.scan_pair(symbol)
            if opportunities:
                results[symbol] = opportunities
            time.sleep(1)  # Пауза между парами
        
        return results
    
    def print_opportunities(self, symbol: str = None):
        """
        Выводит найденные арбитражные возможности
        """
        if symbol:
            symbols = [symbol]
        else:
            symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"🔍 АРБИТРАЖНОЕ СКАНИРОВАНИЕ")
        print(f"Минимальный спред: {self.min_spread}%")
        print(f"{'='*70}")
        
        results = self.scan_all_pairs(symbols)
        
        if not results:
            print(f"{Fore.YELLOW}🤷 Арбитражных возможностей не найдено")
            return
        
        for symbol, opportunities in results.items():
            print(f"\n{Fore.WHITE}{symbol}:")
            for opp in opportunities:
                print(f"{Fore.GREEN}  🟢 ПРЯМОЙ АРБИТРАЖ")
                print(f"     Купить на {opp['buy_exchange']}: ${opp['buy_price']:.2f}")
                print(f"     Продать на {opp['sell_exchange']}: ${opp['sell_price']:.2f}")
                print(f"     Прибыль: ${opp['profit_per_unit']:.2f} на ед. ({opp['spread_percent']:.2f}%)")
    
    def monitor_arbitrage(self, symbols: List[str], interval: int = 30):
        """
        Непрерывный мониторинг арбитража
        """
        print(f"\n{Fore.CYAN}📡 Запуск мониторинга арбитража...")
        
        try:
            while True:
                print(f"\n{Fore.YELLOW}[{time.strftime('%H:%M:%S')}] Сканирование...")
                
                for symbol in symbols:
                    opportunities = self.scan_pair(symbol)
                    
                    if opportunities:
                        for opp in opportunities:
                            print(f"{Fore.GREEN}🚨 АРБИТРАЖ {symbol}: {opp['spread_percent']:.2f}%")
                            print(f"   {opp['buy_exchange']} → {opp['sell_exchange']}")
                    
                    time.sleep(2)  # Пауза между символами
                
                print(f"{Fore.YELLOW}Ожидание {interval} секунд до следующего сканирования...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Мониторинг остановлен пользователем")