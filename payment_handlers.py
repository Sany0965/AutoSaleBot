from telebot import types, TeleBot
import database
import utils
from yoomoney import Quickpay, Client
import config

invoices = {}

def setup_payment_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == 'top_up')
    def top_up_balance(call):
        markup = types.InlineKeyboardMarkup()
        cryptobot_button = types.InlineKeyboardButton(text="🤖 Cryptobot", callback_data='top_up_cryptobot')
        umoney_button = types.InlineKeyboardButton(text="💳 ЮMoney", callback_data='top_up_umoney')
        markup.add(cryptobot_button, umoney_button)
        bot.send_message(call.message.chat.id, "Выберите способ оплаты:", reply_markup=markup)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == 'top_up_cryptobot')
    def top_up_cryptobot(call):
        bot.send_message(call.message.chat.id, "Введите сумму в рублях, на которую вы хотите пополнить баланс (от 5 до 15000 руб):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(call.message, process_top_up_cryptobot_step)
    
    @bot.callback_query_handler(func=lambda call: call.data == 'top_up_umoney')
    def top_up_umoney(call):
        bot.send_message(call.message.chat.id, "Введите сумму в рублях, на которую вы хотите пополнить баланс (от 5 до 15000 руб):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(call.message, process_top_up_umoney_step)
    
    def process_top_up_cryptobot_step(message):
        try:
            amount_rub = float(message.text)
            chat_id = message.chat.id
    
            if amount_rub < 5 or amount_rub > 15000:
                bot.send_message(chat_id, "Сумма пополнения должна быть от 5 до 15000 руб. Попробуйте снова.")
                bot.register_next_step_handler(message, process_top_up_cryptobot_step)
                return
    
            usd_to_rub_rate = utils.get_usd_to_rub_rate()
            if usd_to_rub_rate is None:
                bot.send_message(chat_id, "Ошибка: не удалось получить курс обмена.")
                return
            amount_usd = amount_rub / usd_to_rub_rate
    
            pay_link, invoice_id = utils.get_pay_link(amount_usd)
            if pay_link and invoice_id:
                markup_message = bot.send_message(chat_id, "Перейдите по этой ссылке для оплаты и нажмите 'Проверить оплату' 💸")
                msg = markup_message.message_id
    
                invoices[chat_id] = {'invoice_id': invoice_id, 'amount_rub': amount_rub, 'msg_id': msg, 'status': 'pending'}
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text=f"Оплатить {amount_rub} руб", url=pay_link))
                markup.add(types.InlineKeyboardButton(text="Проверить оплату", callback_data=f'check_payment_cryptobot_{invoice_id}'))
                markup.add(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f'cancel_payment_{invoice_id}'))
    
                bot.edit_message_reply_markup(chat_id, message_id=msg, reply_markup=markup)
            else:
                bot.send_message(chat_id, 'Ошибка: Не удалось создать счет на оплату❌')
    
        except ValueError:
            bot.send_message(message.chat.id, "Ошибка: введите корректную сумму!❌")
            bot.register_next_step_handler(message, process_top_up_cryptobot_step)
    
    def process_top_up_umoney_step(message):
        try:
            amount_rub = float(message.text)
            chat_id = message.chat.id
    
            if amount_rub < 5 or amount_rub > 15000:
                bot.send_message(chat_id, "Сумма пополнения должна быть от 5 до 15000 руб. Попробуйте снова.")
                bot.register_next_step_handler(message, process_top_up_umoney_step)
                return
    
            unique_label = f"{chat_id}_{message.message_id}"
            quickpay = Quickpay(
                receiver=config.YOOMONEY_RECEIVER,
                quickpay_form="shop",
                targets="Пополнение баланса",
                paymentType="SB",
                sum=amount_rub,
                label=unique_label
            )
    
            pay_link = quickpay.redirected_url
            markup_message = bot.send_message(chat_id, "Перейдите по этой ссылке для оплаты и нажмите 'Проверить оплату' 💸")
            msg = markup_message.message_id
    
            invoices[chat_id] = {'label': unique_label, 'amount_rub': amount_rub, 'msg_id': msg, 'status': 'pending'}
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text=f"Оплатить {amount_rub} руб", url=pay_link))
            markup.add(types.InlineKeyboardButton(text="Проверить оплату", callback_data=f'check_payment_umoney_{unique_label}'))
            markup.add(types.InlineKeyboardButton(text="❌ Отмена", callback_data=f'cancel_payment_{unique_label}'))
    
            bot.edit_message_reply_markup(chat_id, message_id=msg, reply_markup=markup)
    
        except ValueError:
            bot.send_message(message.chat.id, "Ошибка: введите корректную сумму!❌")
            bot.register_next_step_handler(message, process_top_up_umoney_step)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('check_payment_cryptobot_'))
    def check_payment_cryptobot(call):
        chat_id = call.message.chat.id
        invoice_id = call.data.split('check_payment_cryptobot_')[1]
        payment_status = utils.check_payment_status(invoice_id)
    
        if payment_status and payment_status.get('ok'):
            if 'items' in payment_status['result']:
                invoice = next((inv for inv in payment_status['result']['items'] if str(inv['invoice_id']) == invoice_id), None)
                if invoice:
                    status = invoice['status']
                    if status == 'paid' and invoices[chat_id]['status'] == 'pending':
                        invoices[chat_id]['status'] = 'paid'
                        bot.send_message(chat_id, "Оплата прошла успешно!✅")
                        
                        conn = database.connect_db()
                        cursor = conn.cursor()
                        
                        amount_rub = invoices[chat_id]['amount_rub']
                        msg_id = invoices[chat_id]['msg_id']
                        cursor.execute('UPDATE users SET balance = balance + ?, total_topups = total_topups + ?, total_topup_count = total_topup_count + 1 WHERE id = ?', (amount_rub, amount_rub, chat_id))
                        conn.commit()
    
                        bot.delete_message(chat_id, msg_id)
                        del invoices[chat_id]
    
                        bot.send_message(chat_id, f"Ваш баланс был успешно пополнен на {amount_rub:.2f} руб! 💸")
                        cursor.close()
                        conn.close()
                    else:
                        bot.answer_callback_query(call.id, 'Оплата не найдена ❌', show_alert=True)
                else:
                    bot.answer_callback_query(call.id, 'Счет не найден.', show_alert=True)
            else:
                print(f"Ответ от API не содержит ключа 'items': {payment_status}")
                bot.answer_callback_query(call.id, 'Ошибка при получении статуса оплаты.', show_alert=True)
        else:
            print(f"Ошибка при запросе статуса оплаты: {payment_status}")
            bot.answer_callback_query(call.id, 'Ошибка при получении статуса оплаты.', show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('check_payment_umoney_'))
    def check_payment_umoney(call):
        chat_id = call.message.chat.id
        label = call.data.split('check_payment_umoney_')[1]
        token = config.YOOMONEY_API_TOKEN  # Ваш API токен ЮMoney
        client = Client(token)
        history = client.operation_history(label=label)
    
        if history.operations:
            operation = next((op for op in history.operations if op.label == label), None)
            if operation and operation.status == 'success' and invoices[chat_id]['status'] == 'pending':
                invoices[chat_id]['status'] = 'paid'
                bot.send_message(chat_id, "Оплата прошла успешно!✅")
                
                conn = database.connect_db()
                cursor = conn.cursor()
                
                amount_rub = invoices[chat_id]['amount_rub']
                msg_id = invoices[chat_id]['msg_id']
                cursor.execute('UPDATE users SET balance = balance + ?, total_topups = total_topups + ?, total_topup_count = total_topup_count + 1 WHERE id = ?', (amount_rub, amount_rub, chat_id))
                conn.commit()

                bot.delete_message(chat_id, msg_id)
                del invoices[chat_id]

                bot.send_message(chat_id, f"Ваш баланс был успешно пополнен на {amount_rub:.2f} руб! 💸")
                cursor.close()
                conn.close()
            else:
                bot.answer_callback_query(call.id, 'Оплата не найдена ❌', show_alert=True)
        else:
            bot.answer_callback_query(call.id, 'Счет не найден.', show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_payment_'))
    def cancel_payment(call):
        chat_id = call.message.chat.id
        
        if chat_id in invoices:
            msg_id = invoices[chat_id]['msg_id']
            del invoices[chat_id]
    
            bot.delete_message(chat_id, msg_id)
    
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        profile_button = types.KeyboardButton("👤 Профиль")
        products_button = types.KeyboardButton("🛍️ Товары")
        markup.add(profile_button, products_button)
    
        bot.send_message(chat_id, "Пополнение баланса отменено. ❌", reply_markup=markup)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == 'gift_balance')
    def gift_balance(call):
        bot.send_message(call.message.chat.id, "Введите ID пользователя, которому вы хотите подарить баланс и затем сумму (пример: 12345678 1.50):", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(call.message, process_gift_balance_step)
    
    def process_gift_balance_step(message):
        try:
            chat_id = message.chat.id
            parts = message.text.split()
            if len(parts) != 2:
                bot.send_message(chat_id, "Неверный формат. Введите данные в формате: ID Сумма (пример: 12345678 1.50)")
                bot.register_next_step_handler(message, process_gift_balance_step)
                return
            
            recipient_id = int(parts[0])
            amount = float(parts[1])
    
            if amount < 0.0:
                bot.send_message(chat_id, "Минимальная сумма перевода 0.20 руб. Попробуйте снова.")
                bot.register_next_step_handler(message, process_gift_balance_step)
                return
    
            conn = database.connect_db()
            cursor = conn.cursor()
    
            cursor.execute('SELECT balance FROM users WHERE id = ?', (chat_id,))
            sender_balance = cursor.fetchone()[0]
    
            if sender_balance < amount:
                bot.send_message(chat_id, "У вас недостаточно средств для перевода. Попробуйте снова.")
                return
            
            cursor.execute('SELECT first_name FROM users WHERE id = ?', (recipient_id,))
            recipient = cursor.fetchone()
    
            if not recipient:
                bot.send_message(chat_id, "Пользователь с указанным ID не найден. Попробуйте снова.")
                return
    
            sender_balance -= amount
            commission = amount * 0.1
            net_amount = amount - commission
    
            cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (sender_balance, chat_id))
            cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (net_amount, recipient_id))
            conn.commit()
    
            sender_name = cursor.execute('SELECT first_name FROM users WHERE id = ?', (chat_id,)).fetchone()[0]
            
            bot.send_message(chat_id, f"Вы успешно перевели {net_amount:.2f} руб пользователю {recipient[0]} 🎉")
            bot.send_message(
                recipient_id,
                f"Вы получили перевод {net_amount:.2f} руб от пользователя {sender_name} 🎉"
            )
            
            cursor.close()
            conn.close()
    
        except ValueError:
            bot.send_message(message.chat.id, "Ошибка: введите корректные данные! ❌")
            bot.register_next_step_handler(message, process_gift_balance_step)
        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)} ❌")
            bot.register_next_step_handler(message, process_gift_balance_step)
