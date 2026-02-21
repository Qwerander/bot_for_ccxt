# exchanges/paper_exchange.py
from typing import Dict, List, Optional
import time
import random
from datetime import datetime
from colorama import Fore, Style

class PaperExchange:
    """Эмуляция биржи для бумажной торговли"""
    
    def __init__(self, initial_balance: float = 10000, fee: float = 0.001, slippage: float = 0.0005):
        self.initial_balance = initial_balance
        self.fee = fee
        self.slippage = slippage
        
        # Начальный портфель
        self.balance = {
            'USDT': {'free': initial_balance, 'used': 0, 'total': initial_balance},
            'BTC': {'free': 0, 'used': 0, 'total': 0},
            'ETH': {'free': 0, 'used': 0, 'total': 0},
        }
        
        # История сделок
        self.trades = []
        
        # Подключение к реальной бирже для получения цен
        from exchanges.connector import ExchangeConnector
        self.real_exchange = ExchangeConnector('bybit')
        
        print(f"{Fore.GREEN}📊 Бумажная биржа создана")
        print(f"Начальный баланс: {initial_balance} USDT")
        print(f"Комиссия: {fee*100}%")
        print(f"Проскальзывание: {slippage*100}%")
    
    def get_ticker(self, symbol: str) -> Dict:
        """Получает текущую цену с реальной биржи"""
        real_ticker = self.real_exchange.get_ticker(symbol)
        if real_ticker:
            return real_ticker
        return None
    
    def get_balance(self) -> Dict:
        """Возвращает текущий баланс"""
        return self.balance
    
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None) -> Dict:
        """
        Создает ордер в бумажной торговле
        order_type: 'market' или 'limit'
        side: 'buy' или 'sell'
        """
        base_currency, quote_currency = symbol.split('/')
        
        # Получаем текущую цену
        ticker = self.get_ticker(symbol)
        if not ticker:
            return {'error': 'Не удалось получить цену'}
        
        # Определяем цену исполнения
        if order_type == 'market':
            if side == 'buy':
                execution_price = ticker['ask'] * (1 + self.slippage)
            else:  # sell
                execution_price = ticker['bid'] * (1 - self.slippage)
        else:  # limit
            if not price:
                return {'error': 'Для лимитного ордера нужна цена'}
            execution_price = price
        
        # Рассчитываем комиссию
        total_value = amount * execution_price
        fee_amount = total_value * self.fee
        
        # Проверяем достаточно ли средств
        if side == 'buy':
            if self.balance[quote_currency]['free'] < total_value + fee_amount:
                return {'error': f'Недостаточно {quote_currency}'}
        else:  # sell
            if self.balance[base_currency]['free'] < amount:
                return {'error': f'Недостаточно {base_currency}'}
        
        # Исполняем ордер
        timestamp = int(time.time() * 1000)
        
        if side == 'buy':
            # Списание средств
            self.balance[quote_currency]['free'] -= (total_value + fee_amount)
            self.balance[quote_currency]['used'] = 0
            self.balance[quote_currency]['total'] = self.balance[quote_currency]['free']
            
            # Зачисление купленного
            self.balance[base_currency]['free'] += amount
            self.balance[base_currency]['total'] = self.balance[base_currency]['free']
            
            trade = {
                'id': len(self.trades) + 1,
                'timestamp': timestamp,
                'datetime': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'type': order_type,
                'side': 'buy',
                'price': execution_price,
                'amount': amount,
                'cost': total_value,
                'fee': fee_amount,
                'total_cost': total_value + fee_amount
            }
        else:  # sell
            # Списание проданного
            self.balance[base_currency]['free'] -= amount
            self.balance[base_currency]['used'] = 0
            self.balance[base_currency]['total'] = self.balance[base_currency]['free']
            
            # Зачисление средств
            self.balance[quote_currency]['free'] += (total_value - fee_amount)
            self.balance[quote_currency]['total'] = self.balance[quote_currency]['free']
            
            trade = {
                'id': len(self.trades) + 1,
                'timestamp': timestamp,
                'datetime': datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'type': order_type,
                'side': 'sell',
                'price': execution_price,
                'amount': amount,
                'cost': total_value,
                'fee': fee_amount,
                'total_received': total_value - fee_amount
            }
        
        self.trades.append(trade)
        
        # Добавляем цвета для вывода
        color = Fore.GREEN if side == 'buy' else Fore.RED
        print(f"{color}📈 Сделка #{trade['id']}: {side.upper()} {amount} {symbol} @ {execution_price:.2f}")
        print(f"   Комиссия: {fee_amount:.2f} {quote_currency}")
        
        return trade
    
    def get_portfolio_value(self) -> Dict:
        """Рассчитывает общую стоимость портфеля"""
        total_value = self.balance['USDT']['free']
        details = {'USDT': self.balance['USDT']['free']}
        
        for currency in ['BTC', 'ETH']:
            if self.balance[currency]['free'] > 0:
                ticker = self.get_ticker(f"{currency}/USDT")
                if ticker:
                    value = self.balance[currency]['free'] * ticker['last']
                    total_value += value
                    details[currency] = value
        
        profit_loss = total_value - self.initial_balance
        profit_loss_percent = (profit_loss / self.initial_balance) * 100
        
        return {
            'total_value': total_value,
            'initial_balance': self.initial_balance,
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent,
            'details': details,
            'trades_count': len(self.trades)
        }
    
    def print_portfolio(self):
        """Красивый вывод портфеля"""
        portfolio = self.get_portfolio_value()
        
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"📊 ПОРТФЕЛЬ (Бумажная торговля)")
        print(f"{'='*50}")
        print(f"Начальный баланс: {portfolio['initial_balance']:.2f} USDT")
        
        color = Fore.GREEN if portfolio['profit_loss'] >= 0 else Fore.RED
        print(f"Текущая стоимость: {portfolio['total_value']:.2f} USDT")
        print(f"P&L: {color}{portfolio['profit_loss']:+.2f} USDT ({portfolio['profit_loss_percent']:+.2f}%)")
        
        print(f"\n{Fore.YELLOW}Детали:")
        for currency, value in portfolio['details'].items():
            if value > 0:
                print(f"  {currency}: {value:.2f} USDT")
        
        print(f"\nСделок: {portfolio['trades_count']}")
        print(f"{Fore.CYAN}{'='*50}\n")
    
    def get_trade_history(self) -> List[Dict]:
        """Возвращает историю сделок"""
        return self.trades
    
    def print_trade_history(self, limit: int = 10):
        """Выводит историю последних сделок"""
        if not self.trades:
            print(f"{Fore.YELLOW}Нет сделок")
            return
        
        print(f"\n{Fore.CYAN}Последние сделки:")
        for trade in self.trades[-limit:]:
            color = Fore.GREEN if trade['side'] == 'buy' else Fore.RED
            print(f"{color}[{trade['datetime']}] {trade['side'].upper()} {trade['amount']} {trade['symbol']} @ {trade['price']:.2f}")