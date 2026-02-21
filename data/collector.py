# data/collector.py
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
from colorama import Fore, Style
import os
from exchanges.connector import ExchangeConnector

class DataCollector:
    """Сбор и обработка исторических данных"""
    
    def __init__(self, exchange_id: str = 'bybit'):
        self.exchange = ExchangeConnector(exchange_id)
        self.data_dir = 'collected_data'
        
        # Создаем директорию для данных если её нет
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 500) -> Optional[pd.DataFrame]:
        """
        Получает исторические свечи (OHLCV)
        timeframe: '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'
        """
        try:
            ohlcv = self.exchange.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"{Fore.RED}Ошибка получения данных {symbol} {timeframe}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, limit: int = 100, force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        Получает исторические данные с кэшированием
        """
        cache_file = f"{self.data_dir}/{symbol.replace('/', '_')}_latest.csv"
        
        # Проверяем кэш
        if not force_refresh and os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 3600:  # Кэш валидн в течение часа
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                print(f"{Fore.GREEN}📂 Данные загружены из кэша ({file_age/60:.1f} мин. назад)")
                return df
        
        # Загружаем свежие данные
        df = self.fetch_ohlcv(symbol, limit=limit)
        
        if df is not None:
            df.to_csv(cache_file)
            print(f"{Fore.GREEN}💾 Данные сохранены в кэш")
        
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Добавляет технические индикаторы
        """
        # Скользящие средние
        df['MA7'] = df['close'].rolling(window=7).mean()
        df['MA25'] = df['close'].rolling(window=25).mean()
        df['MA99'] = df['close'].rolling(window=99).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['Signal']
        
        # Bollinger Bands
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        # Объем
        df['Volume_MA'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def collect_multiple_pairs(self, symbols: List[str], timeframe: str = '1h', limit: int = 100) -> Dict[str, pd.DataFrame]:
        """
        Собирает данные для нескольких пар
        """
        data = {}
        
        for symbol in symbols:
            print(f"{Fore.YELLOW}📊 Загрузка {symbol}...")
            df = self.get_historical_data(symbol, limit)
            if df is not None:
                df = self.add_technical_indicators(df)
                data[symbol] = df
            time.sleep(1)  # Пауза между запросами
        
        return data
    
    def calculate_correlation(self, symbols: List[str], period: str = '1d') -> pd.DataFrame:
        """
        Рассчитывает корреляцию между парами
        """
        prices = {}
        
        for symbol in symbols:
            df = self.get_historical_data(symbol, limit=100)
            if df is not None:
                prices[symbol] = df['close']
        
        if len(prices) > 1:
            price_df = pd.DataFrame(prices)
            correlation = price_df.corr()
            
            print(f"\n{Fore.CYAN}📈 Корреляционная матрица:")
            print(correlation.round(3))
            
            return correlation
        
        return None
    
    def export_to_csv(self, symbol: str, format: str = 'full'):
        """
        Экспортирует данные в CSV
        format: 'full' (все данные) или 'indicators' (только индикаторы)
        """
        df = self.get_historical_data(symbol, limit=500, force_refresh=True)
        
        if df is None:
            return
        
        if format == 'indicators':
            df = self.add_technical_indicators(df)
        
        filename = f"{self.data_dir}/{symbol.replace('/', '_')}_{format}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        df.to_csv(filename)
        
        print(f"{Fore.GREEN}✅ Данные экспортированы в {filename}")
        print(f"   Строк: {len(df)}, колонок: {len(df.columns)}")
        print(f"   Период: {df.index[0]} - {df.index[-1]}")