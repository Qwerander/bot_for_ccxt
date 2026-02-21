# main.py
import sys
import time
from colorama import Fore, Style, init
import argparse

from exchanges.paper_exchange import PaperExchange
from portfolio.tracker import PortfolioTracker
from portfolio.paper_trader import PaperTrader
from monitors.price_alert import PriceAlert
from monitors.arbitrage import ArbitrageScanner
from data.collector import DataCollector
from config import PAPER_TRADING, ALERT_THRESHOLDS, EXCHANGES

# Инициализация colorama для цветного вывода
init(autoreset=True)

class CryptoPaperTradingBot:
    """Главный класс бота для бумажной торговли"""
    
    def __init__(self):
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}🚀 КРИПТО-БОТ (Бумажная торговля)")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Инициализация компонентов
        self.exchange = PaperExchange(
            initial_balance=PAPER_TRADING['initial_balance'],
            fee=PAPER_TRADING['fee_percentage'] / 100,
            slippage=PAPER_TRADING['slippage'] / 100
        )
        
        self.tracker = PortfolioTracker(self.exchange)
        self.trader = PaperTrader(self.exchange)
        self.alert = PriceAlert(self.exchange)
        self.data_collector = DataCollector()
        
        # Начальный снимок портфеля
        self.tracker.snapshot()
        
        print(f"{Fore.GREEN}✅ Бот инициализирован")
        print(f"{Fore.CYAN}{'='*60}\n")
    
    def run_interactive(self):
        """Запускает интерактивный режим"""
        while True:
            self.print_menu()
            choice = input(f"\n{Fore.YELLOW}👉 Выберите действие: ").strip()
            
            if choice == '0':
                print(f"{Fore.GREEN}👋 До свидания!")
                break
            elif choice == '1':
                self.show_portfolio()
            elif choice == '2':
                self.trade_menu()
            elif choice == '3':
                self.alert_menu()
            elif choice == '4':
                self.scan_arbitrage()
            elif choice == '5':
                self.collect_data()
            elif choice == '6':
                self.run_strategy()
            elif choice == '7':
                self.show_history()
            else:
                print(f"{Fore.RED}❌ Неверный выбор")
    
    def print_menu(self):
        """Выводит главное меню"""
        print(f"\n{Fore.CYAN}{'='*40}")
        print(f"{Fore.CYAN}📋 ГЛАВНОЕ МЕНЮ")
        print(f"{Fore.CYAN}{'='*40}")
        print(f"{Fore.WHITE}1.  📊 Показать портфель")
        print(f"2.  💱 Торговля")
        print(f"3.  🔔 Управление оповещениями")
        print(f"4.  🔍 Поиск арбитража")
        print(f"5.  📥 Сбор данных")
        print(f"6.  🤖 Запустить стратегию")
        print(f"7.  📜 История сделок")
        print(f"0.  🚪 Выход")
    
    def show_portfolio(self):
        """Показывает состояние портфеля"""
        self.exchange.print_portfolio()
        self.tracker.print_performance()
    
    def trade_menu(self):
        """Меню торговли"""
        print(f"\n{Fore.CYAN}💱 ТОРГОВЛЯ")
        
        symbol = input("Введите пару (например BTC/USDT): ").strip().upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        print(f"\n1. Купить")
        print(f"2. Продать")
        print(f"0. Назад")
        
        choice = input("Выберите действие: ").strip()
        
        if choice == '0':
            return
        
        side = 'buy' if choice == '1' else 'sell'
        
        try:
            amount = float(input("Введите количество: ").strip())
            order = self.exchange.create_order(symbol, 'market', side, amount)
            
            if order and 'error' not in order:
                self.tracker.snapshot()
            else:
                print(f"{Fore.RED}❌ Ошибка: {order.get('error', 'Неизвестная ошибка')}")
                
        except ValueError:
            print(f"{Fore.RED}❌ Неверное количество")
    
    def alert_menu(self):
        """Меню управления оповещениями"""
        while True:
            print(f"\n{Fore.CYAN}🔔 УПРАВЛЕНИЕ ОПОВЕЩЕНИЯМИ")
            print("1. Добавить оповещение")
            print("2. Список оповещений")
            print("3. Удалить оповещение")
            print("4. Запустить мониторинг")
            print("5. Остановить мониторинг")
            print("0. Назад")
            
            choice = input("Выберите действие: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.add_alert()
            elif choice == '2':
                self.alert.list_alerts()
            elif choice == '3':
                try:
                    alert_id = int(input("ID оповещения: ").strip())
                    self.alert.remove_alert(alert_id)
                except ValueError:
                    print(f"{Fore.RED}❌ Неверный ID")
            elif choice == '4':
                self.alert.start_monitoring()
            elif choice == '5':
                self.alert.stop_monitoring()
    
    def add_alert(self):
        """Добавляет новое оповещение"""
        symbol = input("Пара (например BTC/USDT): ").strip().upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        print("\nТип оповещения:")
        print("1. Выше цены")
        print("2. Ниже цены")
        
        type_choice = input("Выберите: ").strip()
        condition = 'above' if type_choice == '1' else 'below'
        
        try:
            threshold = float(input("Пороговое значение: ").strip())
            message = input("Сообщение (Enter для авто): ").strip()
            
            if not message:
                message = f"{symbol} {condition} {threshold}"
            
            self.alert.add_alert(symbol, condition, threshold, message)
            
        except ValueError:
            print(f"{Fore.RED}❌ Неверное значение")
    
    def scan_arbitrage(self):
        """Сканирует арбитраж"""
        scanner = ArbitrageScanner(
            exchanges=EXCHANGES['secondary'] + [EXCHANGES['primary']],
            min_spread=ALERT_THRESHOLDS['arbitrage_percent']
        )
        
        print("\n1. Быстрое сканирование")
        print("2. Непрерывный мониторинг")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        
        if choice == '1':
            scanner.print_opportunities()
        elif choice == '2':
            try:
                scanner.monitor_arbitrage(['BTC/USDT', 'ETH/USDT'], interval=30)
            except KeyboardInterrupt:
                pass
    
    def collect_data(self):
        """Собирает данные для анализа"""
        print(f"\n{Fore.CYAN}📥 СБОР ДАННЫХ")
        
        symbol = input("Пара (например BTC/USDT): ").strip().upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        df = self.data_collector.get_historical_data(symbol, limit=100, force_refresh=True)
        
        if df is not None:
            df = self.data_collector.add_technical_indicators(df)
            print(f"\n{Fore.GREEN}Последние данные для {symbol}:")
            print(df.tail().round(2))
            
            save = input(f"\nСохранить в CSV? (y/n): ").strip().lower()
            if save == 'y':
                self.data_collector.export_to_csv(symbol, 'indicators')
    
    def run_strategy(self):
        """Запускает торговую стратегию"""
        print(f"\n{Fore.CYAN}🤖 ТОРГОВЫЕ СТРАТЕГИИ")
        print("1. MA Crossover")
        print("2. RSI Strategy")
        print("3. Bollinger Bands")
        print("4. Grid Trading")
        print("0. Назад")
        
        choice = input("Выберите стратегию: ").strip()
        
        if choice == '0':
            return
        
        symbol = input("Пара (например BTC/USDT): ").strip().upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        amount = input("Количество (Enter для авто): ").strip()
        amount = float(amount) if amount else None
        
        strategies = {
            '1': ('ma_crossover', {}),
            '2': ('rsi', {}),
            '3': ('bollinger', {}),
            '4': ('grid', {'grid_levels': 5, 'grid_spacing': 0.02})
        }
        
        if choice in strategies:
            strategy_name, params = strategies[choice]
            self.trader.execute_strategy(strategy_name, symbol, amount, **params)
            self.tracker.snapshot()
    
    def show_history(self):
        """Показывает историю сделок"""
        self.exchange.print_trade_history(limit=20)

def main():
    """Точка входа"""
    parser = argparse.ArgumentParser(description='Крипто-бот для бумажной торговли')
    parser.add_argument('--mode', choices=['interactive', 'strategy'], default='interactive',
                       help='Режим запуска')
    parser.add_argument('--strategy', type=str, help='Стратегия для автоматического режима')
    
    args = parser.parse_args()
    
    bot = CryptoPaperTradingBot()
    
    if args.mode == 'interactive':
        bot.run_interactive()
    elif args.mode == 'strategy' and args.strategy:
        print(f"{Fore.YELLOW}Запуск стратегии {args.strategy} в автоматическом режиме")
        # Здесь можно добавить автоматический режим

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"{Fore.RED}❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()