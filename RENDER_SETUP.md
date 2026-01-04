# ИНСТРУКЦИЯ ПО НАСТРОЙКЕ БОТА НА RENDER

## 1. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ НА RENDER

### Обязательные переменные:
1. **TOKEN**
   - Получить у @BotFather в Telegram
   - Формат: `1234567890:ABCdefGHIjklMnOpQRstUVwxyz`

2. **MONGODB_URI**
   - Получить на MongoDB Atlas
   - Формат: `mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority`

3. **WEBHOOK_URL**
   - URL вашего приложения на Render
   - Формат: `https://your-bot-name.onrender.com`

### Как установить:
1. Зайдите на https://dashboard.render.com
2. Выберите ваше приложение "Monopoly-bot"
3. В меню слева выберите "Environment"
4. Нажмите "Add Environment Variable"
5. Добавьте все 3 переменные

## 2. НАСТРОЙКА MONGODB ATLAS

1. Зайдите на https://cloud.mongodb.com
2. Создайте кластер (бесплатный tier)
3. Добавьте пользователя базы данных
4. Получите строку подключения
5. Добавьте IP-адрес Render в Network Access:
   - Нажмите "Network Access"
   - "Add IP Address"
   - "ALLOW ACCESS FROM ANYWHERE" (0.0.0.0/0)

## 3. ПОСЛЕ НАСТРОЙКИ

1. Перезапустите приложение на Render
2. Проверьте логи на вкладке "Logs"
3. Бот должен запуститься без ошибок
4. Проверьте бота в Telegram: `/start`

## 4. ПРОВЕРКА РАБОТОСПОСОБНОСТИ

1. Откройте в браузере: `https://your-bot-name.onrender.com`
2. Должна открыться страница "Monopoly Telegram Bot"
3. Проверьте API: `https://your-bot-name.onrender.com/api/status`
