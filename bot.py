import logging
import os
from typing import Final

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

IMAGE_BUTTON: Final[str] = "😙"
GIF_BUTTON: Final[str] = "🫳 Pat"
SUPPORT_BUTTON: Final[str] = "🛠️ El Problemo?"
WAITING_SUPPORT_MESSAGE: Final[int] = 1

IMAGE_URL: Final[str] = "https://ibb.co/zVkTdN9S"
GIF_URL: Final[str] = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzlyMGlpZzI5ajh6dmsyYWQyNG5mYmV5bHJsbHJvN3I4NDZuZjJndCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/f2t9SOswHPioJgOFlP/giphy.gif"


def build_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[IMAGE_BUTTON, GIF_BUTTON]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Шо?:",
        reply_markup=build_keyboard(),
    )


async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_photo(photo=IMAGE_URL, reply_markup=build_keyboard())


async def send_gif(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_animation(animation=GIF_URL, reply_markup=build_keyboard())


async def request_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Шо не працює??. Або /cancel якщо все праює.",
        reply_markup=build_keyboard(),
    )
    return WAITING_SUPPORT_MESSAGE


async def forward_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    support_chat_id = os.getenv("SUPPORT_CHAT_ID")
    user = update.effective_user
    message_text = update.message.text

    if support_chat_id:
        support_message = (
            "📩 Новий запит в підтримку\n\n"
            f"Від: {user.full_name} (id: {user.id})\n"
            f"Чат: {update.effective_chat.id}\n\n"
            f"Повідомлення:\n{message_text}"
        )
        await context.bot.send_message(chat_id=int(support_chat_id), text=support_message)
    else:
        logger.warning("SUPPORT_CHAT_ID не задан. Запрос не был отправлен оператору.")

    await update.message.reply_text(
        "Все вирішимо (або зламаємо зовсім).", reply_markup=build_keyboard()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Запрос відкликано. Шо?", reply_markup=build_keyboard()
    )
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Юзай кнопки або команду /start пж.", reply_markup=build_keyboard()
    )


def build_application(token: str) -> Application:
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))

    support_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{SUPPORT_BUTTON}$"), request_support)],
        states={
            WAITING_SUPPORT_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, forward_support_message)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(MessageHandler(filters.Regex(f"^{IMAGE_BUTTON}$"), send_image))
    application.add_handler(MessageHandler(filters.Regex(f"^{GIF_BUTTON}$"), send_gif))
    application.add_handler(support_conversation)
    application.add_handler(MessageHandler(filters.ALL, unknown))

    return application


def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Переменная окружения TELEGRAM_BOT_TOKEN не задана. Установите токен бота."
        )

    application = build_application(token)
    logger.info("Бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()
