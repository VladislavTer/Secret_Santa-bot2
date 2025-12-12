# railway_start.py
import os
import telebot
from flask import Flask, request

# Создаем приложение
app = Flask(__name__)

# Импортируем бота из main
from main import bot, db, start_background_check

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'OK'

@app.route('/health', methods=['GET'])
def health_check():
    return 'OK', 200

if __name__ == '__main__':
    print("🚀 ЗАПУСК ДЛЯ RAILWAY")
    print("=" * 50)
    
    # Получаем порт от Railway
    port = int(os.environ.get('PORT', 5000))
    print(f"📡 Порт: {port}")
    
    # Получаем домен
    domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'secretsanta-bot2-production.up.railway.app')
    webhook_url = f"https://{domain}/webhook"
    print(f"🌐 Домен: {domain}")
    
    # Запускаем фоновую проверку
    start_background_check(bot)
    
    # Устанавливаем вебхук
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"✅ Вебхук установлен: {webhook_url}")
    except Exception as e:
        print(f"⚠️ Ошибка вебхука: {e}")
    
    print("🤖 Бот готов к работе!")
    print("=" * 50)
    
    # Запускаем сервер
    app.run(host='0.0.0.0', port=port, debug=False)
