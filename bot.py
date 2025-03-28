from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import re

# Состояния диалога
GET_PARTICIPANTS_COUNT, GET_EXPENSES = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! Я помогу рассчитать долги между друзьями.\n"
        "Сколько человек участвует?",
    )
    return GET_PARTICIPANTS_COUNT

async def get_participants_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text)
        if count < 2:
            await update.message.reply_text("Должно быть минимум 2 участника!")
            return GET_PARTICIPANTS_COUNT

        context.user_data['participants_count'] = count
        context.user_data['expenses'] = {}

        await update.message.reply_text(
            f"Отлично! Теперь введи траты в формате:\n"
            f"Имя: Сумма\n\n"
            f"Пример:\n"
            f"Вася: 1000\n"
            f"Петя: 500\n"
            f"Маша: 600"
        )
        return GET_EXPENSES

    except ValueError:
        await update.message.reply_text("Пожалуйста, введи число!")
        return GET_PARTICIPANTS_COUNT

def parse_expenses(text):
    expenses = {}
    for line in text.split('\n'):
        match = re.match(r"([А-Яа-яA-Za-z]+):\s*(\d+)", line.strip())
        if match:
            name = match.group(1)
            amount = float(match.group(2))
            expenses[name] = amount
    return expenses

def calculate_debts(expenses):
    total = sum(expenses.values())
    num_people = len(expenses)
    average = total / num_people

    # Разница между оплаченным и средним
    debts = {name: (paid - average) for name, paid in expenses.items()}

    # Кредиторы (кто переплатил) и должники (кто недоплатил)
    creditors = {name: amount for name, amount in debts.items() if amount > 0}
    debtors = {name: -amount for name, amount in debts.items() if amount < 0}

    # Рассчитаем доли кредиторов
    total_credit = sum(creditors.values())
    creditor_shares = {name: (credit / total_credit) for name, credit in creditors.items()}

    transactions = []
    for debtor, debt in debtors.items():
        for creditor, share in creditor_shares.items():
            amount = debt * share
            if amount > 0:
                transactions.append((debtor, creditor, round(amount, 2)))

    # Возвращаем transactions, total и average
    return transactions, total, average

async def get_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    expenses = parse_expenses(text)

    if len(expenses) != context.user_data['participants_count']:
        await update.message.reply_text(
            f"Ожидалось {context.user_data['participants_count']} участников!\n"
            "Пожалуйста, введи данные заново."
        )
        return GET_EXPENSES

    # Получаем transactions, total и average
    transactions, total, average = calculate_debts(expenses)

    # Группируем транзакции по кредиторам
    creditor_transactions = {}
    for debtor, creditor, amount in transactions:
        if creditor not in creditor_transactions:
            creditor_transactions[creditor] = []
        creditor_transactions[creditor].append((debtor, amount))

    # Формируем результат
    result = (
        f"💸 Общая сумма затрат: {total} ₽\n"
        f"🧮 Cумма на одного участника: {round(average, 2)} ₽\n\n"
        f"📊 Результаты расчетов:\n"
    )
    for creditor, debts in creditor_transactions.items():
        result += f"🔹 {creditor}:\n"
        for debtor, amount in debts:
            result += f"   • {debtor} → {creditor}: {amount} ₽\n"
        result += "\n"

    await update.message.reply_text(result)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Диалог отменен")
    return ConversationHandler.END

def main():
    application = Application.builder().token("7385672795:AAEPhVg293ClZnbd0IZbLiaFXDgg2neZ7XM").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_PARTICIPANTS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_participants_count)],
            GET_EXPENSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_expenses)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    app.run_polling()
