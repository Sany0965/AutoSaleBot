from telebot import TeleBot
import config
import admin_handlers
import profile_handlers
import payment_handlers

bot = TeleBot(config.TOKEN)

# Подключаем обработчики
admin_handlers.setup_admin_handlers(bot)
profile_handlers.setup_profile_handlers(bot)
payment_handlers.setup_payment_handlers(bot)

if __name__ == '__main__':
    bot.polling(non_stop=True)
