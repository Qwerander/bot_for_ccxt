# trading_config.py
import os
from dotenv import load_dotenv
from exchanges.paper_exchange import PaperExchange
from exchanges.connector import ExchangeConnector
from colorama import Fore

load_dotenv()

class TradingMode:
    """Класс для переключения между бумажной и реальной торговлей"""
    
    MODE_PAPER = 'paper'
    MODE_REAL = 'real'
    
    def __init__(self, mode=MODE_PAPER, exchange_id='binance'):
        self.mode = mode
        self.exchange_id = exchange_id
        self.exchange = self._create_exchange()
        
    def _create_exchange(self):
        """Создает нужный тип биржи"""
        from config import PAPER_TRADING
        
        if self.mode == self.MODE_PAPER:
            print(f"{Fore.YELLOW}📊 РЕЖИМ: Бумажная торговля")
            return PaperExchange(
                initial_balance=PAPER_TRADING['initial_balance'],
                fee=PAPER_TRADING['fee_percentage'] / 100,
                slippage=PAPER_TRADING['slippage'] / 100
            )
        
        else:  # REAL MODE
            print(f"{Fore.RED}💰 РЕЖИМ: РЕАЛЬНАЯ ТОРГОВЛЯ (ОСТОРОЖНО!)")
            
            # Проверяем наличие ключей
            api_key = os.getenv(f'{self.exchange_id.upper()}_API_KEY')
            secret = os.getenv(f'{self.exchange_id.upper()}_SECRET')
            
            if not api_key or not secret:
                print(f"{Fore.RED}❌ ОШИБКА: Ключи для {self.exchange_id} не найдены!")
                print(f"{Fore.YELLOW}Добавьте их в .env файл:")
                print(f"{self.exchange_id.upper()}_API_KEY=ваш_ключ")
                print(f"{self.exchange_id.upper()}_SECRET=ваш_секрет")
                exit()
            
            # Запрашиваем подтверждение
            print(f"\n{Fore.RED}{'!'*50}")
            print("ВЫ СОБИРАЕТЕСЬ ТОРГОВАТЬ РЕАЛЬНЫМИ ДЕНЬГАМИ!")
            print(f"{'!'*50}")
            confirm = input(f"{Fore.YELLOW}Введите 'YES' для подтверждения: ")
            
            if confirm != 'YES':
                print(f"{Fore.GREEN}Переключено в бумажный режим")
                return PaperExchange(
                    initial_balance=PAPER_TRADING['initial_balance'],
                    fee=PAPER_TRADING['fee_percentage'] / 100,
                    slippage=PAPER_TRADING['slippage'] / 100
                )
            
            # Создаем реальное подключение
            exchange = ExchangeConnector(self.exchange_id, {
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })
            
            # Показываем баланс для подтверждения
            self._show_real_balance(exchange)
            
            return exchange
    
    def _show_real_balance(self, exchange):
        """Показывает реальный баланс"""
        try:
            balance = exchange.get_balance()
            if balance:
                print(f"\n{Fore.CYAN}💰 ВАШ РЕАЛЬНЫЙ БАЛАНС:")
                total = 0
                for currency, amount in balance['total'].items():
                    if amount > 0:
                        try:
                            ticker = exchange.get_ticker(f"{currency}/USDT")
                            if ticker:
                                usd = amount * ticker['last']
                                total += usd
                                print(f"  {currency}: {amount:.8f} ≈ ${usd:.2f}")
                        except:
                            print(f"  {currency}: {amount}")
                
                print(f"{Fore.GREEN}  💵 ОБЩАЯ СТОИМОСТЬ: ~${total:.2f}")
                
                if total < 10:
                    print(f"{Fore.YELLOW}⚠️ На счету меньше $10. Увеличьте баланс для торговли.")
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка получения баланса: {e}")