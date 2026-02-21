# monitors/price_alert.py
import time
import threading
from typing import Dict, List, Callable
from colorama import Fore, Style
from datetime import datetime
from utils.notifications import NotificationManager

class PriceAlert:
    """Мониторинг цен и отправка уведомлений"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.alerts = []
        self.notifier = NotificationManager()
        self.running = False
        self.thread = None
        
    def add_alert(self, symbol: str, condition: str, threshold: float, message: str = None):
        """
        Добавляет ценовое оповещение
        condition: 'above', 'below', 'change_percent'
        """
        alert = {
            'id': len(self.alerts) + 1,
            'symbol': symbol,
            'condition': condition,
            'threshold': threshold,
            'message': message or f"{symbol} {condition} {threshold}",
            'active': True,
            'last_value': None,
            'created_at': datetime.now()
        }
        self.alerts.append(alert)
        print(f"{Fore.GREEN}✅ Оповещение #{alert['id']} добавлено: {alert['message']}")
        return alert['id']
    
    def remove_alert(self, alert_id: int):
        """Удаляет оповещение"""
        self.alerts = [a for a in self.alerts if a['id'] != alert_id]
        print(f"{Fore.YELLOW}🗑️ Оповещение #{alert_id} удалено")
    
    def list_alerts(self):
        """Показывает все активные оповещения"""
        if not self.alerts:
            print(f"{Fore.YELLOW}Нет активных оповещений")
            return
        
        print(f"\n{Fore.CYAN}📋 Активные оповещения:")
        for alert in self.alerts:
            if alert['active']:
                status = f"{Fore.GREEN}Активно"
                last = f", последнее: {alert['last_value']}" if alert['last_value'] else ""
                print(f"  #{alert['id']}: {alert['message']}{last}")
    
    def check_alerts(self):
        """Проверяет все оповещения"""
        for alert in self.alerts:
            if not alert['active']:
                continue
            
            try:
                ticker = self.exchange.get_ticker(alert['symbol'])
                if not ticker:
                    continue
                
                current_price = ticker['last']
                alert['last_value'] = current_price
                
                triggered = False
                
                if alert['condition'] == 'above' and current_price > alert['threshold']:
                    triggered = True
                    message = f"🚨 {alert['symbol']} ПРЕВЫСИЛ {alert['threshold']}! Сейчас: {current_price:.2f}"
                elif alert['condition'] == 'below' and current_price < alert['threshold']:
                    triggered = True
                    message = f"🚨 {alert['symbol']} ОПУСТИЛСЯ НИЖЕ {alert['threshold']}! Сейчас: {current_price:.2f}"
                elif alert['condition'] == 'change_percent':
                    # Для изменения в процентах нужно отслеживать историю
                    pass
                
                if triggered:
                    self.trigger_alert(alert['id'], message)
                    
            except Exception as e:
                print(f"{Fore.RED}Ошибка проверки оповещения #{alert['id']}: {e}")
    
    def trigger_alert(self, alert_id: int, message: str):
        """Активирует оповещение"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                # Отправляем уведомление
                self.notifier.send_notification(message)
                
                # Деактивируем одноразовое оповещение
                alert['active'] = False
                
                print(f"\n{Fore.RED}{'!'*50}")
                print(f"🚨 СРАБОТАЛО ОПОВЕЩЕНИЕ #{alert_id}")
                print(f"{message}")
                print(f"{Fore.RED}{'!'*50}\n")
                break
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Запускает мониторинг в фоне"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,))
        self.thread.daemon = True
        self.thread.start()
        print(f"{Fore.GREEN}📡 Мониторинг цен запущен (интервал: {interval_seconds}с)")
    
    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.running = False
        if self.thread:
            self.thread.join()
        print(f"{Fore.YELLOW}📡 Мониторинг остановлен")
    
    def _monitor_loop(self, interval: int):
        """Основной цикл мониторинга"""
        while self.running:
            self.check_alerts()
            time.sleep(interval)