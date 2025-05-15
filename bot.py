from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# Стадии
AGE_CONFIRM, ASK_NAME, ASK_PHOTO = range(3)

# 🔧 ВСТАВЬ СЮДА СВОЙ ТОКЕН!
BOT_TOKEN = "8089874483:AAFbJ9hnJ71EKGIczU9H0r7mxA2U_vFKHBQ"

# Сохраняем в Google Sheets имя и ссылку на фото
def save_to_google_sheets(name, photo_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Бар-тур Schmidt").sheet1
    sheet.append_row([name, photo_url])

# Получаем прямую ссылку на фото
def get_direct_photo_url(file_id):
    # 1. Получаем file_path через getFile
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
    response = requests.get(url)
    result = response.json()

    if result.get("ok"):
        file_path = result["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    else:
        return "Ошибка получения фото"

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте, это чат-бот *Городские легенды by Schmidt*.\n\n"
        "Здесь вы сможете узнать больше о бренде Schmidt и поучаствовать в бар-туре "
        "«Городские легенды by Schmidt».\n\n"
        "Обещаем — никакого спама. 😊 Жмите на «СТАРТ» и начинайте загадочное путешествие!",
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "Бар-тур *Городские легенды by Schmidt* всё ближе.\n\n"
        "Для продолжения, пожалуйста, подтвердите обработку персональных данных. Вам есть 18 лет?\n\n"
        "Напишите *Да* или *Нет*.",
        parse_mode="Markdown"
    )
    return AGE_CONFIRM

# Подтверждение возраста
async def age_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() != "да":
        await update.message.reply_text("Извините, участие возможно только с 18 лет.")
        return ConversationHandler.END
    await update.message.reply_text("Скажите, как я могу к вам обращаться?")
    return ASK_NAME

# Имя
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()

    await update.message.reply_text(
        f"Рад нашему знакомству, {context.user_data['name']}! 😊\n\n"
        "Вот маршруты бар-тура с городскими легендами и информацией о бренде Schmidt:\n\n"
        "1️⃣ Легенда на Арбате\n"
        "2️⃣ Призрак Бассейной улицы\n"
        "3️⃣ Тайна Маросейки\n"
        "4️⃣ Секрет Воронцова поля\n\n"
        "Выберите маршрут в заведении и получите паспорт участника!"
    )

    await update.message.reply_text(
        "Когда пройдёте бар-тур, загрузите сюда 📸 *фото паспорта участника*, "
        "который вы получили в заведении.",
        parse_mode="Markdown"
    )
    return ASK_PHOTO

# Фото
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        name = context.user_data.get("name", "Не указано")
        photo = update.message.photo[-1]  # Самое большое фото
        photo_file_id = photo.file_id

        # Получаем ссылку на файл
        photo_url = get_direct_photo_url(photo_file_id)

        # Сохраняем в Google Таблицу
        save_to_google_sheets(name, photo_url)

        await update.message.reply_text(
            "Спасибо за фото! 🎉 Вы успешно завершили бар-тур.\n\n"
            "Мы приглашаем вас на финальную вечеринку и участвовать в розыгрыше призов! 🥳"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, загрузите фото паспорта участника 📸.")
        return ASK_PHOTO

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вы завершили диалог. Напишите /start, чтобы начать заново.")
    return ConversationHandler.END

# Запуск
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_confirm)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_photo)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен. Ожидаем пользователей...")
    app.run_polling()

if __name__ == '__main__':
    main()