from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# In-memory shopping list
shopping_list = []


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Shopping List Bot! Use /add <item> to add items, /list to view the list, /remove <item> to remove items, and /clear to clear the list."
    )


async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    item = ' '.join(context.args)
    if item:
        shopping_list.append(item)
        await update.message.reply_text(f"Added '{item}' to the shopping list.")
    else:
        await update.message.reply_text("Usage: /add <item>")


async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not shopping_list:
        await update.message.reply_text("The shopping list is empty.")
        return

    keyboard = [[InlineKeyboardButton(item, callback_data=item)] for item in shopping_list]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Shopping List:", reply_markup=reply_markup)


async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    item = ' '.join(context.args)
    if item in shopping_list:
        shopping_list.remove(item)
        await update.message.reply_text(f"Removed '{item}' from the shopping list.")
    else:
        await update.message.reply_text(f"'{item}' is not in the shopping list.")


async def clear_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    shopping_list.clear()
    await update.message.reply_text("Cleared the shopping list.")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    item = query.data
    if item in shopping_list:
        shopping_list.remove(item)

        if len(shopping_list) > 0:
            keyboard = [[InlineKeyboardButton(item, callback_data=item)] for item in shopping_list]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup)
        else:
            await update.effective_message.edit_reply_markup(None)

    else:
        await query.edit_message_text(f"'{item}' is not in the shopping list.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start - Initialize the bot\n"
        "/add <item> - Add an item to the shopping list\n"
        "/list - Show the current shopping list\n"
        "/remove <item> - Remove an item from the shopping list\n"
        "/clear - Clear the entire shopping list\n"
        "/help - Show this help message"
    )


async def set_commands(application):
    commands = [
        BotCommand("start", "Initialize the bot"),
        BotCommand("add", "Add an item to the shopping list"),
        BotCommand("list", "Show the current shopping list"),
        BotCommand("remove", "Remove an item from the shopping list"),
        BotCommand("clear", "Clear the entire shopping list"),
        BotCommand("help", "Show the list of commands")
    ]
    await application.bot.set_my_commands(commands)


def main() -> None:
    with open("secrets") as f:
        token = f.read()

    application = ApplicationBuilder().token(token).post_init(set_commands).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("list", list_items))
    application.add_handler(CommandHandler("remove", remove_item))
    application.add_handler(CommandHandler("clear", clear_list))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()


if __name__ == '__main__':
    main()
