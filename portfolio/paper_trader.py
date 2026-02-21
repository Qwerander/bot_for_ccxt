# portfolio/paper_trader.py
import time
import random
from typing import Dict, List, Optional
from colorama import Fore, Style
from datetime import datetime
import pandas as pd
import numpy as np

class PaperTrader:
    """Бумажная торговля с различными стратегиями"""
    
    def __init__(self, paper_exchange):
        self.exchange = paper_exchange
        self.positions = {}
        self.strategy_name = "Не выбрана"
        
    def moving_average_crossover(self, symbol: str, short_window: int = 10, long_window: int = 30):
        """
        Стратегия на основе пересечения скользящих средних
        Покупает когда короткая MA пересекает длинную снизу вверх
        Продает когда короткая MA пересекает длинную сверху вниз
        """
        self.strategy_name = f"MA Crossover ({short_window}/{long_window})"
        
        # Получаем исторические данные
        from data.collector import DataCollector
        collector = DataCollector()
        df = collector.get_historical_data(symbol, limit=long_window + 10)
        
        if df is None or len(df) < long_window:
            return None
        
        # Рассчитываем скользящие средние
        df['MA_short'] = df['close'].rolling(window=short_window).mean()
        df['MA_long'] = df['close'].rolling(window=long_window).mean()
        
        # Проверяем пересечение
        if len(df) >= 2:
            prev_cross = df['MA_short'].iloc[-2] - df['MA_long'].iloc[-2]
            curr_cross = df['MA_short'].iloc[-1] - df['MA_long'].iloc[-1]
            
            # Пересечение снизу вверх (сигнал к покупке)
            if prev_cross < 0 and curr_cross > 0:
                return {'action': 'buy', 'reason': 'MA bullish crossover'}
            
            # Пересечение сверху вниз (сигнал к продаже)
            elif prev_cross > 0 and curr_cross < 0:
                return {'action': 'sell', 'reason': 'MA bearish crossover'}
        
        return None
    
    def rsi_strategy(self, symbol: str, period: int = 14, oversold: int = 30, overbought: int = 70):
        """
        Стратегия на основе RSI (Relative Strength Index)
        Покупает когда RSI < oversold (перепроданность)
        Продает когда RSI > overbought (перекупленность)
        """
        self.strategy_name = f"RSI ({period}, {oversold}/{overbought})"
        
        # Получаем исторические данные
        from data.collector import DataCollector
        collector = DataCollector()
        df = collector.get_historical_data(symbol, limit=period + 10)
        
        if df is None or len(df) < period + 1:
            return None
        
        # Рассчитываем RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < oversold:
            return {'action': 'buy', 'reason': f'RSI oversold ({current_rsi:.1f})'}
        elif current_rsi > overbought:
            return {'action': 'sell', 'reason': f'RSI overbought ({current_rsi:.1f})'}
        
        return None
    
    def bollinger_bands(self, symbol: str, period: int = 20, std_dev: float = 2):
        """
        Стратегия на основе полос Боллинджера
        Покупает когда цена касается нижней полосы
        Продает когда цена касается верхней полосы
        """
        self.strategy_name = f"Bollinger Bands ({period}, {std_dev})"
        
        # Получаем исторические данные
        from data.collector import DataCollector
        collector = DataCollector()
        df = collector.get_historical_data(symbol, limit=period + 10)
        
        if df is None or len(df) < period:
            return None
        
        # Рассчитываем полосы Боллинджера
        df['MA'] = df['close'].rolling(window=period).mean()
        df['std'] = df['close'].rolling(window=period).std()
        df['Upper'] = df['MA'] + (df['std'] * std_dev)
        df['Lower'] = df['MA'] - (df['std'] * std_dev)
        
        current_price = df['close'].iloc[-1]
        current_lower = df['Lower'].iloc[-1]
        current_upper = df['Upper'].iloc[-1]
        
        if current_price <= current_lower:
            return {'action': 'buy', 'reason': f'Price touched lower band ({current_price:.2f} <= {current_lower:.2f})'}
        elif current_price >= current_upper:
            return {'action': 'sell', 'reason': f'Price touched upper band ({current_price:.2f} >= {current_upper:.2f})'}
        
        return None
    
    def simple_grid(self, symbol: str, grid_levels: int = 5, grid_spacing: float = 0.02):
        """
        Простая сеточная стратегия
        Размещает ордера на покупку ниже текущей цены и на продажу выше
        """
        self.strategy_name = f"Grid ({grid_levels} levels, {grid_spacing*100}% spacing)"
        
        ticker = self.exchange.get_ticker(symbol)
        if not ticker:
            return None
        
        current_price = ticker['last']
        balance = self.exchange.get_balance()
        
        base_currency, quote_currency = symbol.split('/')
        
        # Определяем количество для каждого ордера
        base_amount = balance[quote_currency]['free'] * 0.2 / current_price  # 20% от баланса на первый ордер
        
        signals = []
        
        # Ордера на покупку ниже текущей цены
        for i in range(1, grid_levels + 1):
            buy_price = current_price * (1 - i * grid_spacing)
            signals.append({
                'action': 'buy_limit',
                'price': buy_price,
                'amount': base_amount,
                'reason': f'Grid buy level {i}'
            })
        
        # Ордера на продажу выше текущей цены
        for i in range(1, grid_levels + 1):
            sell_price = current_price * (1 + i * grid_spacing)
            signals.append({
                'action': 'sell_limit',
                'price': sell_price,
                'amount': base_amount * 0.5,  # Меньше на продажу так как может не быть монет
                'reason': f'Grid sell level {i}'
            })
        
        return signals
    
    def execute_strategy(self, strategy: str, symbol: str, amount: float = None, **kwargs):
        """
        Выполняет выбранную стратегию
        """
        print(f"\n{Fore.CYAN}📊 Стратегия: {self.strategy_name}")
        
        # Получаем сигнал от стратегии
        if strategy == 'ma_crossover':
            signal = self.moving_average_crossover(symbol, **kwargs)
        elif strategy == 'rsi':
            signal = self.rsi_strategy(symbol, **kwargs)
        elif strategy == 'bollinger':
            signal = self.bollinger_bands(symbol, **kwargs)
        elif strategy == 'grid':
            signals = self.simple_grid(symbol, **kwargs)
            if signals:
                for signal in signals:
                    self._execute_signal(signal, symbol, amount)
            return
        else:
            print(f"{Fore.RED}❌ Неизвестная стратегия: {strategy}")
            return
        
        # Выполняем сигнал
        if signal:
            self._execute_signal(signal, symbol, amount)
        else:
            print(f"{Fore.YELLOW}⏸️ Нет сигнала к действию")
    
    def _execute_signal(self, signal, symbol, amount=None):
        """Выполняет торговый сигнал"""
        if isinstance(signal, dict) and 'action' in signal:
            action = signal['action']
            reason = signal.get('reason', 'No reason')
            
            print(f"{Fore.YELLOW}📢 Сигнал: {action.upper()} - {reason}")
            
            # Определяем количество для торговли
            if amount is None:
                balance = self.exchange.get_balance()
                base_currency, quote_currency = symbol.split('/')
                
                if action == 'buy':
                    # Используем 10% от доступного баланса
                    amount = balance[quote_currency]['free'] * 0.1 / self.exchange.get_ticker(symbol)['last']
                elif action == 'sell':
                    # Продаем 10% от имеющихся монет
                    amount = balance[base_currency]['free'] * 0.1
            
            if action == 'buy':
                self.exchange.create_order(symbol, 'market', 'buy', amount)
            elif action == 'sell':
                self.exchange.create_order(symbol, 'market', 'sell', amount)
            elif action == 'buy_limit':
                self.exchange.create_order(symbol, 'limit', 'buy', amount, signal['price'])
            elif action == 'sell_limit':
                self.exchange.create_order(symbol, 'limit', 'sell', amount, signal['price'])