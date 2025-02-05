from telebot import types
import database

def setup_profile_handlers(bot):
    @bot.message_handler(commands=['start'])
    def welcome(message):
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        conn = database.connect_db()
        cursor = conn.cursor()

        # Добавляем нового пользователя в базу данных, если его там нет
        cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)', (user_id, username, first_name))
            conn.commit()

        cursor.close()
        conn.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        profile_button = types.KeyboardButton("👤 Профиль")
        products_button = types.KeyboardButton("🛍️ Товары")
        markup.add(profile_button, products_button)
        
        bot.send_message(message.chat.id, f"Добро пожаловать, {first_name}! 👋 Нажмите кнопку ниже, чтобы перейти к профилю или посмотреть товары.", reply_markup=markup)

    @bot.message_handler(commands=['cancel'])
    def cancel(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        profile_button = types.KeyboardButton("👤 Профиль")
        products_button = types.KeyboardButton("🛍️ Товары")
        markup.add(profile_button, products_button)
        
        bot.send_message(message.chat.id, "Операция отменена. Вы в главном меню.", reply_markup=markup)

    @bot.message_handler(regexp="👤 Профиль")
    def profile(message):
        user_id = message.from_user.id
        
        conn = database.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            user_id = user[0]
            username = user[1]
            first_name = user[2]
            balance = user[3]
            total_topups = user[4]
            total_purchases = user[5]
            
            markup = types.InlineKeyboardMarkup()
            top_up_button = types.InlineKeyboardButton(text="💸 Пополнить баланс", callback_data='top_up')
            gift_balance_button = types.InlineKeyboardButton(text="🎁 Подарить баланс", callback_data='gift_balance')
            markup.add(top_up_button, gift_balance_button)
            
            bot.send_message(
                message.chat.id,
                f"Ваш профиль:\nID: {user_id}\n👤 Юзернейм: @{username}\n📛 Имя: {first_name}\n💰 Баланс: {balance:.2f} руб\n💸 Сумма пополнений: {total_topups:.2f} руб\n🛒 Количество покупок: {total_purchases}",
                reply_markup=markup
            )

    @bot.message_handler(regexp="🛍️ Товары")
    def products(message):
        conn = database.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products')
        product_list = cursor.fetchall()

        cursor.close()
        conn.close()

        if not product_list:
            bot.send_message(message.chat.id, "Пока нет доступных товаров.")
            return

        markup = types.InlineKeyboardMarkup()
        for product in product_list:
            markup.add(types.InlineKeyboardButton(text=product[1], callback_data=f'view_product_{product[0]}'))

        bot.send_message(message.chat.id, "Доступные товары:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('view_product_'))
    def view_product(call):
        product_id = int(call.data.split('_')[2])
        
        conn = database.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not product:
            bot.send_message(call.message.chat.id, "Товар не найден.")
            return
        
        product_name = product[1]
        price = product[2]
        file_id = product[3]
        description = product[4]

        file_info = bot.get_file(file_id)
        file_type = file_info.file_path.split('.')[-1]

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Купить", callback_data=f'buy_product_{product_id}_{call.message.message_id}'))
        markup.add(types.InlineKeyboardButton(text="Назад", callback_data=f'back_to_products_{call.message.message_id}'))

        product_message = bot.send_message(
            call.message.chat.id,
            f"Название товара: {product_name}\nОписание: {description}\nТип товара: Файл {file_type.upper()}\nЦена: {price:.2f} руб",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_products_'))
    def back_to_products(call):
        data = call.data.split('_')
        original_message_id = int(data[-1])
        bot.delete_message(call.message.chat.id, original_message_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        products(call.message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_product_'))
    def buy_product(call):
        data = call.data.split('_')
        product_id = int(data[2])
        original_message_id = int(data[-1])
        user_id = call.message.chat.id
        
        conn = database.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            bot.send_message(user_id, "Товар не найден.")
            return

        product_name = product[1]
        price = product[2]
        file_id = product[3]
        
        cursor.execute('SELECT balance, total_purchases FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        user_balance = user_data[0]
        total_purchases = user_data[1]
        
        if user_balance < price:
            bot.send_message(user_id, "У вас недостаточно средств для покупки этого товара.")
            return

        cursor.execute('UPDATE users SET balance = balance - ?, total_purchases = total_purchases + 1 WHERE id = ?', (price, user_id))
        conn.commit()
        
        bot.send_document(user_id, file_id, caption=f"Вы успешно приобрели {product_name} за {price:.2f} руб.")

        bot.delete_message(call.message.chat.id, original_message_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        cursor.close()
        conn.close()
