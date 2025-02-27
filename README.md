
# Telegram Shop Bot 🤖

Telegram-бот для управления профилем пользователя, пополнения баланса, покупки товаров и администрирования. Поддерживает интеграцию с Cryptobot и ЮMoney.

---

## 🚀 Особенности
- **Пользователи**:
  - Просмотр профиля (баланс, история пополнений, покупки).
  - Пополнение баланса через Cryptobot или ЮMoney.
  - Перевод средств другим пользователям.
  - Просмотр и покупка товаров.

- **Администраторы**:
  - Управление товарами (добавление, удаление, редактирование).
  - Просмотр пользователей с пагинацией.
  - Изменение баланса пользователей.
  - Рассылка сообщений всем пользователям.

---

## 🛠 Технологии
- **Библиотеки**:
  - `telebot` — работа с Telegram API.
  - `sqlite3` — хранение данных пользователей и товаров.
  - `requests` — взаимодействие с API платежных систем.
  - `yoomoney` — интеграция с ЮMoney.

- **Платежные системы**:
  - **Cryptobot** — криптовалютные платежи.
  - **ЮMoney** — фиатные платежи.

---

## 📦 Установка
1. Скачайте репозиторий:
   ```bash
   скачайте архив с ботом
   ```

2. Установите зависимости:
   ```bash
   библиотеки 
   ```

3. Настройте `config.py`:
   - `TOKEN` — токен вашего Telegram-бота.
   - `ADMIN_ID` — ID администратора.
   - `YOOMONEY_RECEIVER` и `YOOMONEY_API_TOKEN` — данные ЮMoney.
   - `CRYPTOPAY_API_TOKEN` — токен Cryptobot.

4. Запустите бота:
   ```bash
   python bot.py
   ```

---

## 📋 Команды
| Команда/Кнопка           | Описание                          | Доступ         |
|--------------------------|-----------------------------------|----------------|
| `/start`                 | Начало работы с ботом.            | Все пользователи |
| `/admin`                 | Открыть админ-панель.             | Администратор   |
| `/off`                   | Выйти из админ-панели.            | Администратор   |
| 👤 Профиль               | Просмотр профиля.                 | Все пользователи |
| 🛍️ Товары               | Просмотр доступных товаров.       | Все пользователи |
| 💸 Пополнить баланс      | Выбор способа пополнения.         | Все пользователи |
| 🎁 Подарить баланс       | Перевод средств другому пользователю. | Все пользователи |

**Админ-панель**:
- 📢 Рассылка — отправить сообщение всем пользователям.
- 💰 Изменить баланс — изменить баланс пользователя по ID.
- 👥 Количество пользователей — просмотр списка пользователей.
- ➕ Добавить товар / ❌ Удалить товар / ✏️ Редактировать товар — управление товарами.

---

## 📄 Лицензия
Проект распространяется под лицензией [MIT](LICENSE).

---

## 🤝 Контакты
Если у вас есть вопросы или предложения, свяжитесь со мной:  
💬 Telegram: @worpli
```
