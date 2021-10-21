#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import Update, ForceReply 
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters 
from telegram.ext import CallbackContext, ConversationHandler

from django.core.management.base import BaseCommand
from django.conf import settings

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


NUMBER_LEVELS, FORM, ADDRESS = range(3)


# Dialogue keyboards
def main_keyboard(chat_id):
    if not Profile.objects.get(user_id__contains=chat_id):
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Регистрация'),
                ]
            ],
            resize_keyboard=True
        )
        return markup
    else:
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Собрать торт'),
                    KeyboardButton(text='Ваши заказы')
                ]
            ],
            resize_keyboard=True
        )
        return markup


def agreement_keyboard():
    markup = ReplyKeyboardMarkup(
        keybord=[
            [
                KeyboardButton(text='Добавить телефон'),
                KeyboardButton(text='Отказаться')
            ]
        ],
        resize_keyboard=True
    )
    return markup


def registration_keyboard():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Согласиться'),
                KeyboardButton(text='Отказаться'),
            ]
        ],
        resize_keyboard=True
    )
    return markup


def order_cake_keyboard():
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Заказать торт'),
                KeyboardButton(text='В главное меню'),
            ]
        ],
        resize_keyboard=True
    )
    return markup


# Cake composition
def levels_keyboard():
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('1 уровень (+400р)', callback_data='+400р'),
                InlineKeyboardButton('2 уровня (+750р)', callback_data='+750р'),
                InlineKeyboardButton('3 уровня (+1100р)', callback_data='+1100р'),
            ]
        ]
    )
    return markup


def form_keyboard():
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Квадрат (+600)', callback_data='+ 600р'),
                InlineKeyboardButton('Круг (+400)', callback_data='+ 400р'),
                InlineKeyboardButton('Прямоугольник (+1000)', callback_data='+1000р'),
            ]
        ]
    )
    return markup


def topping_keyboard():
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton('Без топпинга (+0)', callback_data='+ 0р'),
                InlineKeyboardButton('Белый соус (+200)', callback_data='+ 200р'),
                InlineKeyboardButton('Карамельный сироп (+180)', callback_data='+ 180р'),
                InlineKeyboardButton('Клубничный сироп (+300)', callback_data='+ 300р'),
                InlineKeyboardButton('Черничный сироп (+350)', callback_data='+ 350р'),
                InlineKeyboardButton('Молочный шоколад (+200)', callback_data='+ 200р'),
            ]
        ]
    )
    return markup


# Define a few command handlers. These usually take the two arguments update
# and context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


# user registration
def registration_handler(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.message.text == 'Регистрация':
        # Отправка файла из папки files
        file_handler(chat_id)
        context.bot.send_message(
            chat_id=chat_id,
            text='Ознакомьтесь с политикой по обработке персональных данных.',
            reply_markup=registration_keyboard()
        )

    if update.message.text == 'Согласиться':
        user_first_name = update.effective_message.chat.first_name
        user_lst_name = update.effective_message.chat.last_name
        context.bot.send_message(
            chat_id=chat_id,
            text='Добавьте свой номер телефона',
            reply_markup=order_cake_keyboard()
        )
    # <- Добавить функцию записи user_registration_db()

    if update.message.text == 'Добавить телефон':
        user_input = update.edited_message.text
        if user_input.isdigit():    
            context.bot.send_message(
                chat_id=chat_id,
                text='Добавьте адрес доставки.',
                reply_markup=order_cake_keyboard()
            )
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text='Номер телефона указан не верно.'
                     'Он должен содержать только числа.'
                     'Повторите ввод!',
                reply_markup=order_cake_keyboard()
            )

    if update.message.text == 'Отказаться':
        context.bot.send_message(
            chat_id=chat_id,
            text='К сожалению, мы не сможем приготовить Вам торт :((.',
            reply_markup=main_keyboard(chat_id)
        )


def file_handler(context, chat_id):
    with open('../../files/personal_data_policy.pdf', 'rb') as file:
        return context.bot.send_document(chat_id, file)


def user_registration_db():
    pass


# Place an order or redirect the main menu
def order_cake_handler(update, context):
    pass


def cancel_handler(update, context):
    # user = update.effective_user
    update.message.reply_text(
        'Очень жаль, что вы отменили заказ :((. Возвращайтесь!'
    )
    return ConversationHandler.END


def run_bot(tg_token) -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(tg_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Dialogue system for ordering a cake
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(Filters.text, order_cake_handler),
        ],
        states={
            NUMBER_LEVELS: [
                MessageHandler(
                    Filters.regex('^1 уровень&'),
                    callback,
                    pass_user_data=True
                ),
                MessageHandler(
                    Filters.regex('^2 уровня&'),
                    callback,
                    pass_user_data=True
                ),
                MessageHandler(
                    Filters.regex('^3 уровня&'),
                    callback,
                    pass_user_data=True
                ),
            ],
            FORM: [
                MessageHandler(Filters.text, callback, pass_user_data=True)
            ],
            ADDRESS: [
                MessageHandler(Filters.text, callback, pass_user_data=True)
            ]
        },
        fallbacks=[
            MessageHandler(Filters.text, cancel_handler)

        ],
    )

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # user registration
    dispatcher.add_handler(
        MessageHandler(
            Filters.regex('^Регистрация&'),
            callback=registration_handler
        )
    )

    dispatcher.add_handler(
        MessageHandler(
            Filters.regex('^Согласиться&'),
            callback=registration_handler
        )
    )

    dispatcher.add_handler(
        MessageHandler(
            Filters.regex('^Отказаться&'),
            callback=registration_handler
        )
    )

    # Dialogue system for ordering a cake
    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


class Command(BaseCommand):
    help = 'Import module with telegram bot code'

    def handle(self, *args, **options):
        run_bot(settings.TG_TOKEN)
