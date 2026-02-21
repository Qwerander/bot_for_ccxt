# portfolio/tracker.py
from typing import Dict, List, Optional
from colorama import Fore, Style
from tabulate import tabulate
import pandas as pd
from datetime import datetime
import time

class PortfolioTracker:
    """Трекер для отслеживания портфеля и его эффективности"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.history = []
        self.start_time = datetime.now()
        self.is_paper = hasattr(exchange, 'paper_mode')  # Определяем тип биржи
        
    def get_portfolio_value(self) -> Dict:
        """Получает стоимость портфеля (работает с любым типом биржи)"""
        
        if self.is_paper:
            # Для бумажной биржи
            return self.exchange.get_portfolio_value()
        else:
            # Для реальной биржи
            return self._get_real_portfolio_value()
    
    def _get_real_portfolio_value(self) -> Dict:
        """Рассчитывает стоимость реального портфеля"""
        try:
            balance = self.exchange.get_balance()
            if not balance:
                return {
                    'total_value': 0,
                    'initial_balance': 0,
                    'profit_loss': 0,
                    'profit_loss_percent': 0,
                    'details': {},
                    'trades_count': 0
                }
            
            total_value = 0
            details = {}
            
            # Считаем USDT отдельно
            usdt_amount = balance['total'].get('USDT', 0)
            if usdt_amount > 0:
                total_value += usdt_amount
                details['USDT'] = usdt_amount
            
            # Считаем другие монеты
            for currency, amount in balance['total'].items():
                if currency != 'USDT' and amount > 0:
                    try:
                        ticker = self.exchange.get_ticker(f"{currency}/USDT")
                        if ticker and ticker.get('last'):
                            value = amount * ticker['last']
                            total_value += value
                            details[currency] = value
                    except:
                        # Если не можем получить цену, пропускаем
                        pass
            
            # Для реальной торговли нет понятия "начальный баланс"
            # Возвращаем текущую стоимость как базовую
            
            return {
                'total_value': total_value,
                'initial_balance': total_value,  # Для реальной - текущий = начальный
                'profit_loss': 0,
                'profit_loss_percent': 0,
                'details': details,
                'trades_count': 0  # Для реальной не считаем сделки через бота
            }
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка получения стоимости портфеля: {e}")
            return {
                'total_value': 0,
                'initial_balance': 0,
                'profit_loss': 0,
                'profit_loss_percent': 0,
                'details': {},
                'trades_count': 0
            }
    
    def snapshot(self):
        """Создает снимок текущего состояния портфеля"""
        portfolio = self.get_portfolio_value()
        
        # Для реальной торговли считаем P&L относительно первого снимка
        if not self.is_paper and len(self.history) > 0:
            first_value = self.history[0]['total_value']
            current_value = portfolio['total_value']
            portfolio['profit_loss'] = current_value - first_value
            portfolio['profit_loss_percent'] = (current_value - first_value) / first_value * 100 if first_value > 0 else 0
            portfolio['initial_balance'] = first_value
        
        snapshot = {
            'timestamp': datetime.now(),
            'total_value': portfolio['total_value'],
            'profit_loss': portfolio['profit_loss'],
            'profit_loss_percent': portfolio['profit_loss_percent'],
            'trades_count': portfolio['trades_count'],
            'details': portfolio['details'].copy()
        }
        self.history.append(snapshot)
        return snapshot
    
    def print_portfolio_summary(self, portfolio: Dict):
        """Выводит сводку по портфелю"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"📊 ПОРТФЕЛЬ {'(Реальный)' if not self.is_paper else '(Бумажный)'}")
        print(f"{'='*50}")
        
        if self.is_paper:
            print(f"Начальный баланс: {portfolio['initial_balance']:.2f} USDT")
        
        color = Fore.GREEN if portfolio['profit_loss'] >= 0 else Fore.RED
        print(f"Текущая стоимость: {portfolio['total_value']:.2f} USDT")
        
        if portfolio['profit_loss'] != 0:
            print(f"P&L: {color}{portfolio['profit_loss']:+.2f} USDT ({portfolio['profit_loss_percent']:+.2f}%)")
        
        print(f"\n{Fore.YELLOW}Детали:")
        for currency, value in portfolio['details'].items():
            if value > 0:
                print(f"  {currency}: {value:.2f} USDT")
        
        if self.is_paper:
            print(f"\nСделок: {portfolio['trades_count']}")
        
        print(f"{Fore.CYAN}{'='*50}\n")
    
    def get_performance_metrics(self) -> Dict:
        """Рассчитывает метрики производительности"""
        if len(self.history) < 2:
            return {}
        
        first = self.history[0]
        last = self.history[-1]
        
        # Временной период
        time_diff = (last['timestamp'] - first['timestamp']).total_seconds() / 3600  # в часах
        
        # Общая доходность
        total_return = last['profit_loss_percent']
        
        # Среднечасовая доходность
        hourly_return = total_return / time_diff if time_diff > 0 else 0
        
        # Максимальная просадка
        peak = max(h['total_value'] for h in self.history)
        current_drawdown = (peak - last['total_value']) / peak * 100 if peak > 0 else 0
        
        # Волатильность (стандартное отклонение доходности)
        returns = []
        for i in range(1, len(self.history)):
            prev_value = self.history[i-1]['total_value']
            if prev_value > 0:
                ret = (self.history[i]['total_value'] - prev_value) / prev_value
                returns.append(ret)
        
        volatility = pd.Series(returns).std() * 100 if len(returns) > 1 else 0
        
        return {
            'total_return': total_return,
            'hourly_return': hourly_return,
            'current_drawdown': current_drawdown,
            'volatility': volatility,
            'trades_count': last['trades_count'],
            'trading_hours': time_diff,
            'peak_value': peak,
            'current_value': last['total_value']
        }
    
    def print_performance(self):
        """Выводит метрики производительности"""
        metrics = self.get_performance_metrics()
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"📈 ПРОИЗВОДИТЕЛЬНОСТЬ ПОРТФЕЛЯ")
        print(f"{'='*60}")
        
        if not metrics:
            print(f"{Fore.YELLOW}Недостаточно данных для анализа")
            return
        
        # Форматируем вывод
        color_return = Fore.GREEN if metrics['total_return'] >= 0 else Fore.RED
        
        if metrics['total_return'] != 0:
            print(f"Общая доходность: {color_return}{metrics['total_return']:+.2f}%")
            print(f"Среднечасовая: {metrics['hourly_return']:+.3f}%")
        
        color_drawdown = Fore.RED if metrics['current_drawdown'] > 10 else Fore.YELLOW if metrics['current_drawdown'] > 5 else Fore.GREEN
        print(f"Текущая просадка: {color_drawdown}{metrics['current_drawdown']:.2f}%")
        
        if metrics['volatility'] > 0:
            print(f"Волатильность: {metrics['volatility']:.2f}%")
        
        print(f"Время торговли: {metrics['trading_hours']:.1f} часов")
        
        if metrics['trades_count'] > 0:
            print(f"Сделок: {metrics['trades_count']}")
        
        # Прогресс бар для визуализации доходности (только если есть изменение)
        if metrics['total_return'] != 0:
            print(f"\n{Fore.YELLOW}Прогресс:")
            bar_length = 30
            progress = (metrics['total_return'] + 100) / 200  # от -100% до +100%
            progress = max(0, min(1, progress))
            
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"[{bar}] {metrics['total_return']:+.2f}%")
        
        print(f"{Fore.CYAN}{'='*60}\n")