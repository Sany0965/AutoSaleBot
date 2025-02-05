from telebot import types
import config
import database
import telebot

conn = database.connect_db()
cursor = conn.cursor()

admin_mode = {}
product_step = {}
products = {}
users_page = {}

# Добавление функции для показа пользователей с пагинацией
def show_users_page(bot, chat_id, page_number):
    conn = database.connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    if total_users == 0:
        bot.send_message(chat_id, "Пользователей нет.")
        return

    cursor.execute('SELECT id, username, first_name, balance, total_topups, total_purchases FROM users LIMIT 10 OFFSET ?', ((page_number - 1) * 10,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    users_info = "\n\n".join([
        f"🆔ID: `{escape_markdown(str(user[0]))}`\n👤 Юзернейм: @{escape_markdown(str(user[1]))}\n📛 Имя: {escape_markdown(str(user[2]))}\n💰 Баланс: {user[3]:.2f} руб\n💸 Сумма пополнений: {user[4]:.2f} руб\n🛒 Количество покупок: {user[5]}"
        for user in users
    ])

    markup = types.InlineKeyboardMarkup()
    if page_number > 1:
        markup.add(types.InlineKeyboardButton(text="⏪ Влево", callback_data=f'users_page_{page_number - 1}'))
    if (page_number * 10) < total_users:
        markup.add(types.InlineKeyboardButton(text="⏩ Вправо", callback_data=f'users_page_{page_number + 1}'))

    bot.send_message(chat_id, f"Количество пользователей: {total_users}\n\n{users_info}", reply_markup=markup, parse_mode='Markdown')

def escape_markdown(text):
    escape_chars = r'\*_`['
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def send_main_menu(bot, chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    profile_button = types.KeyboardButton("👤 Профиль")
    products_button = types.KeyboardButton("🛍️ Товары")
    markup.add(profile_button, products_button)
    bot.send_message(chat_id, "Вы в главном меню.", reply_markup=markup)

def setup_admin_handlers(bot):
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id == config.ADMIN_ID:
            admin_mode[message.from_user.id] = True
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            broadcast_button = types.KeyboardButton("📢 Рассылка")
            change_balance_button = types.KeyboardButton("💰 Изменить баланс")
            user_count_button = types.KeyboardButton("👥 Количество пользователей")
            add_product_button = types.KeyboardButton("➕ Добавить товар")
            delete_product_button = types.KeyboardButton("❌ Удалить товар")
            edit_product_button = types.KeyboardButton("✏️ Редактировать товар")
            exit_button = types.KeyboardButton("❌ Выйти")
            markup.add(broadcast_button, change_balance_button, user_count_button, add_product_button, delete_product_button, edit_product_button, exit_button)
            bot.send_message(message.chat.id, "Админ панель:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")

    @bot.message_handler(commands=['off'])
    def exit_admin_panel(message):
        if message.from_user.id in admin_mode:
            del admin_mode[message.from_user.id]
        send_main_menu(bot, message.chat.id)
        bot.send_message(message.chat.id, "Вы вышли из админ панели.")

    @bot.message_handler(func=lambda message: message.from_user.id in admin_mode)
    def admin_actions(message):
        chat_id = message.chat.id
        
        if message.text == "📢 Рассылка":
            bot.send_message(chat_id, "Введите текст для рассылки:")
            bot.register_next_step_handler(message, broadcast_message)
            
        elif message.text == "💰 Изменить баланс":
            bot.send_message(chat_id, "Введите ID пользователя, чей баланс вы хотите изменить:")
            bot.register_next_step_handler(message, get_user_balance)

        elif message.text == "👥 Количество пользователей":
            users_page[chat_id] = 1
            show_users_page(bot, chat_id, users_page[chat_id])

        elif message.text == "➕ Добавить товар":
            bot.send_message(chat_id, "Введите имя товара:")
            bot.register_next_step_handler(message, process_product_name)
    
        elif message.text == "❌ Удалить товар":
            cursor.execute('SELECT * FROM products')
            product_list = cursor.fetchall()
            if not product_list:
                bot.send_message(chat_id, "Товаров нет.")
                return

            markup = types.InlineKeyboardMarkup()
            for product in product_list:
                markup.add(types.InlineKeyboardButton(text=product[1], callback_data=f'delete_product_{product[0]}'))
            bot.send_message(chat_id, "Выберите товар для удаления:", reply_markup=markup)

        elif message.text == "✏️ Редактировать товар":
            select_product_to_edit(message)

        elif message.text == "❌ Выйти":
            exit_admin_panel(message)
        
        else:
            bot.send_message(message.chat.id, "Неизвестная команда. Пожалуйста, выберите одну из опций.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('users_page_'))
    def change_users_page(call):
        page_number = int(call.data.split('_')[2])
        users_page[call.message.chat.id] = page_number
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_users_page(bot, call.message.chat.id, page_number)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_product_'))
    def delete_product(call):
        product_id = int(call.data.split('_')[2])
        
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        
        bot.send_message(call.message.chat.id, "Товар успешно удален.")
    
    # Определение функции select_product_to_edit
    def select_product_to_edit(message):
        cursor.execute('SELECT * FROM products')
        product_list = cursor.fetchall()
        if not product_list:
            bot.send_message(message.chat.id, "Товаров нет.")
            return

        markup = types.InlineKeyboardMarkup()
        for product in product_list:
            markup.add(types.InlineKeyboardButton(text=product[1], callback_data=f'edit_product_{product[0]}'))
        bot.send_message(message.chat.id, "Выберите товар для редактирования:", reply_markup=markup)
    
    # Обработчики для редактирования товара
    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_product_'))
    def edit_product(call):
        product_id = int(call.data.split('_')[2])
        product_step[call.message.chat.id] = {'id': product_id}
        bot.send_message(call.message.chat.id, "Введите новое имя товара или * чтобы оставить прежним:")
        bot.register_next_step_handler(call.message, process_new_product_name)

    def process_new_product_name(message):
        new_name = message.text
        chat_id = message.chat.id
        if new_name != "*":
            product_step[chat_id]['name'] = new_name
        bot.send_message(chat_id, "Введите новое описание товара или * чтобы оставить прежним:")
        bot.register_next_step_handler(message, process_new_product_description)

    def process_new_product_description(message):
        new_description = message.text
        chat_id = message.chat.id
        if new_description != "*":
            product_step[chat_id]['description'] = new_description
        bot.send_message(chat_id, "Введите новую цену товара или * чтобы оставить прежним:")
        bot.register_next_step_handler(message, process_new_product_price)

    def process_new_product_price(message):
        new_price = message.text
        chat_id = message.chat.id
        if new_price != "*":
            try:
                product_step[chat_id]['price'] = float(new_price)
            except ValueError:
                bot.send_message(chat_id, "Неверный формат цены. Попробуйте снова.")
                bot.register_next_step_handler(message, process_new_product_price)
                return
        bot.send_message(chat_id, "Пришлите новый файл товара или * чтобы оставить прежним:")
        bot.register_next_step_handler(message, process_new_product_file)

    def process_new_product_file(message):
        chat_id = message.chat.id
        if message.document:
            product_step[chat_id]['file_id'] = message.document.file_id
        update_product_in_db(chat_id)

    def update_product_in_db(chat_id):
        product_data = product_step.get(chat_id, {})
        product_id = product_data.get('id')

        if not product_id:
            bot.send_message(chat_id, "Произошла ошибка. Попробуйте снова.")
            return

        conn = database.connect_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, description, price, file_id FROM products WHERE id = ?', (product_id,))
        current_data = cursor.fetchone()

        if 'name' in product_data:
            cursor.execute('UPDATE products SET name = ? WHERE id = ?', (product_data['name'], product_id))
        if 'description' in product_data:
            cursor.execute('UPDATE products SET description = ? WHERE id = ?', (product_data['description'], product_id))
        if 'price' in product_data:
            cursor.execute('UPDATE products SET price = ? WHERE id = ?', (product_data['price'], product_id))
        if 'file_id' in product_data:
            cursor.execute('UPDATE products SET file_id = ? WHERE id = ?', (product_data['file_id'], product_id))
        else:
            # Если поле file_id не изменилось, используем текущее значение
            cursor.execute('UPDATE products SET file_id = ? WHERE id = ?', (current_data[3], product_id))

        conn.commit()
        cursor.close()
        conn.close()

        bot.send_message(chat_id, "Товар успешно обновлен.")
        product_step.pop(chat_id, None)
    
    def broadcast_message(message):
        # Проверяем, если сообщение содержит команду, то отменяем действие
        if message.text.startswith('/'):
            bot.send_message(message.chat.id, "Рассылка отменена.")
            return

        broadcast_text = message.text
        cursor.execute('SELECT id FROM users')
        user_ids = cursor.fetchall()
        
        for user_id in user_ids:
            try:
                bot.send_message(user_id[0], f"Сообщение от админа: {broadcast_text}")
            except telebot.apihelper.ApiTelegramException as e:
                if e.error_code == 403:
                    # Пользователь заблокировал бота, пропускаем этого пользователя
                    print(f"Пользователь {user_id[0]} заблокировал бота, сообщение не отправлено.")
                else:
                    raise e
        
        bot.send_message(message.chat.id, "Рассылка завершена.")
    
    def get_user_balance(message):
        # Проверяем, если сообщение содержит команду, то отменяем действие
        if message.text.startswith('/'):
            bot.send_message(message.chat.id, "Изменение баланса отменено.")
            return
        
        try:
            user_id = int(message.text)
            cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                username = user[1]
                first_name = user[2]
                balance = user[3]
                user_id = user[0]
                
                markup = types.InlineKeyboardMarkup()
                change_balance_button = types.InlineKeyboardButton(text="Изменить баланс", callback_data=f'change_balance_{user_id}')
                markup.add(change_balance_button)
                
                bot.send_message(
                    message.chat.id,
                    f"Профиль пользователя:\nID: `{escape_markdown(str(user_id))}`\n👤 Юзернейм: @{escape_markdown(str(username))}\n📛 Имя: {escape_markdown(str(first_name))}\n💰 Баланс: {balance:.2f} руб",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            else:
                bot.send_message(message.chat.id, "Пользователь с таким ID не найден.")
            
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат ID. Попробуйте снова.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('change_balance_'))
    def change_balance(call):
        user_id = int(call.data.split('_')[2])
        bot.send_message(call.message.chat.id, "Введите новый баланс для пользователя:")
        bot.register_next_step_handler(call.message, update_user_balance, user_id)

    def update_user_balance(message, user_id):
        try:
            new_balance = float(message.text)
            cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
            conn.commit()
            
            bot.send_message(message.chat.id, "Баланс успешно обновлен.")
            bot.send_message(user_id, f"Администратор изменил ваш баланс. Новый баланс: {new_balance:.2f} руб")
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат суммы. Попробуйте снова.")

    def process_product_name(message):
        admin_id = message.from_user.id
        product_step[admin_id] = {}
        product_step[admin_id]['name'] = message.text
        bot.send_message(message.chat.id, "Введите цену товара:")
        bot.register_next_step_handler(message, process_product_price)

    def process_product_price(message):
        admin_id = message.from_user.id
        try:
            price = float(message.text)
            product_step[admin_id]['price'] = price
            bot.send_message(message.chat.id, "Введите описание товара:")
            bot.register_next_step_handler(message, process_product_description)
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат цены. Попробуйте снова.")
            bot.register_next_step_handler(message, process_product_price)

    def process_product_description(message):
        admin_id = message.from_user.id
        product_step[admin_id]['description'] = message.text
        bot.send_message(message.chat.id, "Пришлите сам товар (файл):")
        bot.register_next_step_handler(message, process_product_file)

    def process_product_file(message):
        admin_id = message.from_user.id
        if message.document:
            file_id = message.document.file_id
            product_step[admin_id]['file_id'] = file_id
            
            # Сохраняем товар в базу данных
            cursor.execute('INSERT INTO products (name, price, file_id, description) VALUES (?, ?, ?, ?)',
                           (product_step[admin_id]['name'], product_step[admin_id]['price'], product_step[admin_id]['file_id'], product_step[admin_id]['description']))
            conn.commit()
            
            bot.send_message(message.chat.id, "Товар успешно добавлен.")
            del product_step[admin_id]
        else:
            bot.send_message(message.chat.id, "Ошибка: это не файл. Попробуйте снова.")
            bot.register_next_step_handler(message, process_product_file)
