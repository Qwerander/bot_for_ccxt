# main.py
import sys
import time
import argparse
from colorama import Fore, Style, init
from trading_config import TradingMode
from portfolio.tracker import PortfolioTracker
from portfolio.paper_trader import PaperTrader
from monitors.price_alert import PriceAlert
from monitors.arbitrage import ArbitrageScanner
from data.collector import DataCollector
from config import PAPER_TRADING, ALERT_THRESHOLDS, EXCHANGES

init(autoreset=True)

class CryptoBot:
    """Главный класс бота с поддержкой реальной торговли"""
    
    def __init__(self, mode='paper', exchange='binance'):
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}🚀 КРИПТО-ТОРГОВЫЙ БОТ")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Создаем биржу в нужном режиме
        self.trading_mode = TradingMode(mode, exchange)
        self.exchange = self.trading_mode.exchange
        
        # Инициализация компонентов
        self.tracker = PortfolioTracker(self.exchange)
        self.trader = PaperTrader(self.exchange)
        self.alert = PriceAlert(self.exchange)
        self.data_collector = DataCollector(exchange_id=exchange)
        
        # Начальный снимок портфеля
        self.tracker.snapshot()
        
        print(f"{Fore.GREEN}✅ Бот инициализирован")
        print(f"{Fore.CYAN}{'='*60}\n")
    
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
        print(f"8.  ⚙️  Настройки")
        print(f"0.  🚪 Выход")
    
    def show_portfolio(self):
        """Показывает состояние портфеля"""
        portfolio = self.tracker.get_portfolio_value()
        self.tracker.print_portfolio_summary(portfolio)
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
            
            # Проверка для реальной торговли
            if hasattr(self.exchange, 'exchange') and not hasattr(self.exchange, 'paper_mode'):
                ticker = self.exchange.get_ticker(symbol)
                if ticker:
                    trade_value = amount * ticker['last']
                    from config import RISK_MANAGEMENT
                    if trade_value > RISK_MANAGEMENT['max_trade_size_usdt']:
                        print(f"{Fore.RED}❌ Сделка отклонена: превышен максимальный размер")
                        print(f"   Максимум: ${RISK_MANAGEMENT['max_trade_size_usdt']}")
                        print(f"   Запрошено: ${trade_value:.2f}")
                        return
                    
                    confirm = input(f"{Fore.YELLOW}Подтвердите сделку на ${trade_value:.2f} (yes/no): ")
                    if confirm.lower() != 'yes':
                        print(f"{Fore.YELLOW}Сделка отменена")
                        return
            
            order = self.exchange.create_order(symbol, 'market', side, amount)
            
            if order and 'error' not in order:
                self.tracker.snapshot()
                print(f"{Fore.GREEN}✅ Сделка выполнена успешно!")
            else:
                print(f"{Fore.RED}❌ Ошибка: {order.get('error', 'Неизвестная ошибка')}")
                
        except ValueError:
            print(f"{Fore.RED}❌ Неверное количество")
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка: {e}")
    
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
                interval = input("Интервал проверки в секундах (Enter для 60): ").strip()
                interval = int(interval) if interval else 60
                self.alert.start_monitoring(interval)
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
        print("3. Изменение % за 1ч")
        
        type_choice = input("Выберите: ").strip()
        
        if type_choice == '1':
            condition = 'above'
        elif type_choice == '2':
            condition = 'below'
        elif type_choice == '3':
            condition = 'change_percent'
        else:
            print(f"{Fore.RED}❌ Неверный выбор")
            return
        
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
        # Собираем список бирж для сканирования
        exchanges_to_scan = [EXCHANGES['primary']] + EXCHANGES['secondary']
        
        scanner = ArbitrageScanner(
            exchanges=exchanges_to_scan,
            min_spread=ALERT_THRESHOLDS['arbitrage_percent']
        )
        
        print(f"\n{Fore.CYAN}🔍 АРБИТРАЖНОЕ СКАНИРОВАНИЕ")
        print("1. Быстрое сканирование (BTC, ETH, BNB)")
        print("2. Сканировать конкретную пару")
        print("3. Непрерывный мониторинг")
        print("0. Назад")
        
        choice = input("Выберите: ").strip()
        
        if choice == '1':
            scanner.print_opportunities()
        elif choice == '2':
            symbol = input("Введите пару (например BTC/USDT): ").strip().upper()
            if '/' not in symbol:
                symbol = f"{symbol}/USDT"
            scanner.print_opportunities(symbol)
        elif choice == '3':
            try:
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
                scanner.monitor_arbitrage(symbols, interval=30)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Мониторинг остановлен")
    
    def collect_data(self):
        """Собирает данные для анализа"""
        print(f"\n{Fore.CYAN}📥 СБОР ДАННЫХ")
        
        symbol = input("Пара (например BTC/USDT): ").strip().upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        print("\nТаймфрейм:")
        print("1. 1 минута")
        print("2. 5 минут")
        print("3. 15 минут")
        print("4. 1 час")
        print("5. 4 часа")
        print("6. 1 день")
        
        tf_choice = input("Выберите: ").strip()
        
        timeframe_map = {
            '1': '1m',
            '2': '5m',
            '3': '15m',
            '4': '1h',
            '5': '4h',
            '6': '1d'
        }
        
        timeframe = timeframe_map.get(tf_choice, '1h')
        
        limit = input("Количество свечей (Enter для 100): ").strip()
        limit = int(limit) if limit else 100
        
        df = self.data_collector.get_historical_data(symbol, limit=limit, force_refresh=True)
        
        if df is not None:
            df = self.data_collector.add_technical_indicators(df)
            print(f"\n{Fore.GREEN}✅ Данные загружены:")
            print(f"   Период: {df.index[0]} - {df.index[-1]}")
            print(f"   Свечей: {len(df)}")
            
            print(f"\n{Fore.CYAN}Последние данные:")
            print(df.tail().round(2))
            
            save = input(f"\n{Fore.YELLOW}Сохранить в CSV? (y/n): ").strip().lower()
            if save == 'y':
                self.data_collector.export_to_csv(symbol, 'indicators')
                
            analyze = input(f"\n{Fore.YELLOW}Показать статистику? (y/n): ").strip().lower()
            if analyze == 'y':
                self.analyze_data(df, symbol)
    
    def analyze_data(self, df, symbol):
        """Анализирует собранные данные"""
        print(f"\n{Fore.CYAN}📊 СТАТИСТИКА {symbol}")
        print(f"{'='*50}")
        
        # Основная статистика
        print(f"Средняя цена: ${df['close'].mean():.2f}")
        print(f"Максимум: ${df['high'].max():.2f}")
        print(f"Минимум: ${df['low'].min():.2f}")
        print(f"Волатильность: {df['close'].pct_change().std() * 100:.2f}%")
        
        # Тренд
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) > 50 else None
        
        if sma_50 and sma_20 > sma_50:
            print(f"{Fore.GREEN}📈 Тренд: Восходящий (SMA20 > SMA50)")
        elif sma_50:
            print(f"{Fore.RED}📉 Тренд: Нисходящий (SMA20 < SMA50)")
        
        # RSI
        if 'RSI' in df.columns:
            current_rsi = df['RSI'].iloc[-1]
            if current_rsi < 30:
                print(f"{Fore.GREEN}📊 RSI: {current_rsi:.1f} - Перепроданность (сигнал к покупке)")
            elif current_rsi > 70:
                print(f"{Fore.RED}📊 RSI: {current_rsi:.1f} - Перекупленность (сигнал к продаже)")
            else:
                print(f"{Fore.YELLOW}📊 RSI: {current_rsi:.1f} - Нейтрально")
    
    def run_strategy(self):
        """Запускает торговую стратегию"""
        print(f"\n{Fore.CYAN}🤖 ТОРГОВЫЕ СТРАТЕГИИ")
        print("1. MA Crossover (пересечение скользящих средних)")
        print("2. RSI Strategy (индекс относительной силы)")
        print("3. Bollinger Bands (полосы Боллинджера)")
        print("4. Grid Trading (сеточная торговля)")
        print("0. Назад")
        
        choice = input("Выберите стратегию: ").strip()
        
        if choice == '0':
            return
        
        symbol = input("Пара (например BTC/USDT): ").strip().upper()
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        amount = input("Количество (Enter для авто-расчета): ").strip()
        amount = float(amount) if amount else None
        
        # Дополнительные параметры для стратегий
        if choice == '1':  # MA Crossover
            short = input("Короткий период MA (Enter для 10): ").strip()
            long = input("Длинный период MA (Enter для 30): ").strip()
            
            short = int(short) if short else 10
            long = int(long) if long else 30
            
            self.trader.execute_strategy('ma_crossover', symbol, amount, 
                                        short_window=short, long_window=long)
        
        elif choice == '2':  # RSI
            period = input("Период RSI (Enter для 14): ").strip()
            oversold = input("Уровень перепроданности (Enter для 30): ").strip()
            overbought = input("Уровень перекупленности (Enter для 70): ").strip()
            
            period = int(period) if period else 14
            oversold = int(oversold) if oversold else 30
            overbought = int(overbought) if overbought else 70
            
            self.trader.execute_strategy('rsi', symbol, amount,
                                        period=period, oversold=oversold, overbought=overbought)
        
        elif choice == '3':  # Bollinger Bands
            period = input("Период (Enter для 20): ").strip()
            std = input("Стандартных отклонений (Enter для 2): ").strip()
            
            period = int(period) if period else 20
            std = float(std) if std else 2.0
            
            self.trader.execute_strategy('bollinger', symbol, amount,
                                        period=period, std_dev=std)
        
        elif choice == '4':  # Grid Trading
            levels = input("Количество уровней сетки (Enter для 5): ").strip()
            spacing = input("Шаг сетки в % (Enter для 2): ").strip()
            
            levels = int(levels) if levels else 5
            spacing = float(spacing) / 100 if spacing else 0.02
            
            self.trader.execute_strategy('grid', symbol, amount,
                                        grid_levels=levels, grid_spacing=spacing)
        
        # Обновляем портфель после стратегии
        self.tracker.snapshot()
    
    def show_history(self):
        """Показывает историю сделок"""
        print(f"\n{Fore.CYAN}📜 ИСТОРИЯ СДЕЛОК")
        self.exchange.print_trade_history(limit=20)
        
        # Показываем статистику по сделкам
        trades = self.exchange.get_trade_history()
        if trades:
            buys = [t for t in trades if t['side'] == 'buy']
            sells = [t for t in trades if t['side'] == 'sell']
            
            print(f"\n{Fore.YELLOW}Статистика:")
            print(f"  Всего сделок: {len(trades)}")
            print(f"  Покупок: {len(buys)}")
            print(f"  Продаж: {len(sells)}")
            
            if buys and sells:
                total_invested = sum(t.get('cost', 0) for t in buys)
                total_received = sum(t.get('total_received', t.get('cost', 0)) for t in sells)
                profit = total_received - total_invested
                
                if profit != 0:
                    color = Fore.GREEN if profit > 0 else Fore.RED
                    print(f"  Прибыль/убыток: {color}${profit:.2f}")
    
    def settings_menu(self):
        """Меню настроек"""
        while True:
            print(f"\n{Fore.CYAN}⚙️  НАСТРОЙКИ")
            print("1. Показать текущие настройки")
            print("2. Изменить начальный баланс (бумажная торговля)")
            print("3. Изменить комиссию")
            print("4. Изменить проскальзывание")
            print("5. Сбросить портфель (бумажная торговля)")
            print("0. Назад")
            
            choice = input("Выберите: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.show_settings()
            elif choice == '2':
                if hasattr(self.exchange, 'paper_mode'):
                    new_balance = float(input("Новый начальный баланс USDT: "))
                    self.exchange.initial_balance = new_balance
                    self.exchange.balance['USDT']['free'] = new_balance
                    self.exchange.balance['USDT']['total'] = new_balance
                    print(f"{Fore.GREEN}✅ Баланс изменен")
                else:
                    print(f"{Fore.RED}❌ Недоступно в реальном режиме")
            elif choice == '3':
                if hasattr(self.exchange, 'paper_mode'):
                    new_fee = float(input("Новая комиссия в %: "))
                    self.exchange.fee = new_fee / 100
                    print(f"{Fore.GREEN}✅ Комиссия изменена")
                else:
                    print(f"{Fore.RED}❌ Недоступно в реальном режиме")
            elif choice == '4':
                if hasattr(self.exchange, 'paper_mode'):
                    new_slippage = float(input("Новое проскальзывание в %: "))
                    self.exchange.slippage = new_slippage / 100
                    print(f"{Fore.GREEN}✅ Проскальзывание изменено")
                else:
                    print(f"{Fore.RED}❌ Недоступно в реальном режиме")
            elif choice == '5':
                if hasattr(self.exchange, 'paper_mode'):
                    confirm = input(f"{Fore.RED}Сбросить портфель? (yes/no): ")
                    if confirm.lower() == 'yes':
                        self.exchange = self.trading_mode._create_exchange()
                        self.tracker = PortfolioTracker(self.exchange)
                        print(f"{Fore.GREEN}✅ Портфель сброшен")
                else:
                    print(f"{Fore.RED}❌ Недоступно в реальном режиме")
    
    def show_settings(self):
        """Показывает текущие настройки"""
        print(f"\n{Fore.CYAN}ТЕКУЩИЕ НАСТРОЙКИ")
        print(f"{'='*50}")
        
        mode = "РЕАЛЬНАЯ ТОРГОВЛЯ" if hasattr(self.exchange, 'exchange') else "БУМАЖНАЯ ТОРГОВЛЯ"
        color = Fore.RED if mode == "РЕАЛЬНАЯ ТОРГОВЛЯ" else Fore.GREEN
        print(f"Режим: {color}{mode}")
        
        if hasattr(self.exchange, 'paper_mode'):
            print(f"Начальный баланс: ${self.exchange.initial_balance}")
            print(f"Комиссия: {self.exchange.fee * 100}%")
            print(f"Проскальзывание: {self.exchange.slippage * 100}%")
        else:
            print(f"Биржа: {self.exchange.exchange_id}")
            from config import RISK_MANAGEMENT
            print(f"Макс. размер сделки: ${RISK_MANAGEMENT['max_trade_size_usdt']}")
            print(f"Макс. дневной убыток: ${RISK_MANAGEMENT['max_daily_loss_usdt']}")
    
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
            elif choice == '8':
                self.settings_menu()
            else:
                print(f"{Fore.RED}❌ Неверный выбор")

def main():
    """Точка входа"""
    parser = argparse.ArgumentParser(description='Крипто-торговый бот')
    parser.add_argument('--mode', choices=['paper', 'real'], default='paper',
                       help='paper - бумажная торговля, real - реальная')
    parser.add_argument('--exchange', type=str, default='binance',
                       help='ID биржи (binance, bybit, kucoin и др.)')
    
    args = parser.parse_args()
    
    # Предупреждение для реального режима
    if args.mode == 'real':
        print(f"\n{Fore.RED}{'⚠️'*50}")
        print("⚠️  ВНИМАНИЕ: ВЫ ВХОДИТЕ В РЕЖИМ РЕАЛЬНОЙ ТОРГОВЛИ!")
        print("⚠️  Все сделки будут выполняться с реальными деньгами!")
        print("⚠️  Убедитесь что вы протестировали стратегии в бумажном режиме!")
        print(f"{Fore.RED}{'⚠️'*50}\n")
        
        confirm = input(f"{Fore.YELLOW}Введите 'I UNDERSTAND' для продолжения: ")
        if confirm != 'I UNDERSTAND':
            print(f"{Fore.GREEN}Переключение в бумажный режим...")
            args.mode = 'paper'
        
        time.sleep(1)
    
    try:
        bot = CryptoBot(mode=args.mode, exchange=args.exchange)
        bot.run_interactive()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"{Fore.RED}❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()