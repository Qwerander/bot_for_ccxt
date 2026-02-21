# utils/notifications.py
import smtplib
import requests
from typing import List, Dict
from colorama import Fore, Style
import os

class NotificationManager:
    """Управление уведомлениями"""
    
    def __init__(self):
        self.notification_history = []
        
    def send_notification(self, message: str, method: str = 'console'):
        """
        Отправляет уведомление выбранным методом
        method: 'console', 'email', 'telegram'
        """
        if method == 'console':
            self._console_notification(message)
        elif method == 'email':
            self._email_notification(message)
        elif method == 'telegram':
            self._telegram_notification(message)
        
        # Сохраняем в историю
        self.notification_history.append({
            'message': message,
            'method': method,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def _console_notification(self, message: str):
        """Вывод в консоль"""
        print(f"\n{Fore.MAGENTA}🔔 УВЕДОМЛЕНИЕ: {message}{Style.RESET_ALL}")
    
    def _email_notification(self, message: str):
        """Отправка email (требуется настройка)"""
        # Пример для Gmail
        try:
            sender = os.getenv('EMAIL_SENDER', '')
            password = os.getenv('EMAIL_PASSWORD', '')
            recipient = os.getenv('EMAIL_RECIPIENT', '')
            
            if not all([sender, password, recipient]):
                print(f"{Fore.YELLOW}⚠️ Email не настроен. Укажите EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT в .env")
                return
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender, password)
            
            subject = "Крипто-уведомление"
            body = f"Subject: {subject}\n\n{message}"
            
            server.sendmail(sender, recipient, body)
            server.quit()
            
            print(f"{Fore.GREEN}✅ Email отправлен")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка отправки email: {e}")
    
    def _telegram_notification(self, message: str):
        """Отправка Telegram сообщения"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
            chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
            
            if not all([bot_token, chat_id]):
                print(f"{Fore.YELLOW}⚠️ Telegram не настроен. Укажите TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env")
                return
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ Telegram сообщение отправлено")
            else:
                print(f"{Fore.RED}❌ Ошибка отправки Telegram: {response.text}")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка отправки Telegram: {e}")
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Возвращает историю уведомлений"""
        return self.notification_history[-limit:]