# portfolio/tracker.py
from typing import Dict, List, Optional
from colorama import Fore, Style
from tabulate import tabulate
import pandas as pd
from datetime import datetime

class PortfolioTracker:
    """Трекер для отслеживания портфеля и его эффективности"""
    
    def __init__(self, paper_exchange):
        self.exchange = paper_exchange
        self.history = []
        self.start_time = datetime.now()
        
    def snapshot(self):
        """Создает снимок текущего состояния портфеля"""
        portfolio = self.exchange.get_portfolio_value()
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
        current_drawdown = (peak - last['total_value']) / peak * 100
        
        # Волатильность (стандартное отклонение доходности)
        returns = []
        for i in range(1, len(self.history)):
            ret = (self.history[i]['total_value'] - self.history[i-1]['total_value']) / self.history[i-1]['total_value']
            returns.append(ret)
        
        volatility = pd.Series(returns).std() * 100 if returns else 0
        
        # Коэффициент Шарпа (упрощенно)
        risk_free_rate = 2.0  # 2% годовых
        sharpe = (total_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        return {
            'total_return': total_return,
            'hourly_return': hourly_return,
            'current_drawdown': current_drawdown,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
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
        
        print(f"Общая доходность: {color_return}{metrics['total_return']:+.2f}%")
        print(f"Среднечасовая: {metrics['hourly_return']:+.3f}%")
        
        color_drawdown = Fore.RED if metrics['current_drawdown'] > 10 else Fore.YELLOW if metrics['current_drawdown'] > 5 else Fore.GREEN
        print(f"Текущая просадка: {color_drawdown}{metrics['current_drawdown']:.2f}%")
        
        print(f"Волатильность: {metrics['volatility']:.2f}%")
        print(f"Коэффициент Шарпа: {metrics['sharpe_ratio']:.2f}")
        print(f"Сделок: {metrics['trades_count']}")
        print(f"Время торговли: {metrics['trading_hours']:.1f} часов")
        
        # Прогресс бар для визуализации доходности
        print(f"\n{Fore.YELLOW}Прогресс:")
        bar_length = 30
        progress = (metrics['total_return'] + 100) / 200  # от -100% до +100%
        progress = max(0, min(1, progress))
        
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"[{bar}] {metrics['total_return']:+.2f}%")
        
        print(f"{Fore.CYAN}{'='*60}\n")
    
    def export_history(self, filename: str = "portfolio_history.csv"):
        """Экспортирует историю в CSV"""
        if not self.history:
            print(f"{Fore.YELLOW}Нет данных для экспорта")
            return
        
        data = []
        for snap in self.history:
            row = {
                'timestamp': snap['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'total_value': snap['total_value'],
                'profit_loss': snap['profit_loss'],
                'profit_loss_percent': snap['profit_loss_percent'],
                'trades_count': snap['trades_count']
            }
            # Добавляем детали по валютам
            for currency, value in snap['details'].items():
                row[f'{currency}_value'] = value
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"{Fore.GREEN}✅ История экспортирована в {filename}")