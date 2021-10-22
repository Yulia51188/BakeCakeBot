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
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackContext, ConversationHandler

from django.core.management.base import BaseCommand
from django.conf import settings

from bake_cake_bot.models import Client
from enum import Enum

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


class States(Enum):
    WHAITING_CLICK = 0
    LAYERS = 1
    FORM = 2
    TOPPING = 3
    BERRIES = 4
    DECOR = 5
    LETTERING = 6
    ADDRESS = 7


# Dialogue keyboards
# def main_keyboard(chat_id):
#     # if not Profile.objects.get(user_id__contains=chat_id):
#     if chat_id:
#         markup = ReplyKeyboardMarkup(
#             keyboard=[
#                 [
#                     KeyboardButton(text='Регистрация'),
#                 ]
#             ],
#             resize_keyboard=True
#         )
#         return markup
#     else:
#         markup = ReplyKeyboardMarkup(
#             keyboard=[
#                 [
#                     KeyboardButton(text='Собрать торт'),
#                     KeyboardButton(text='Ваши заказы')
#                 ]
#             ],
#             resize_keyboard=True
#         )
#         return markup


# def contact_keyboard():
#     markup = ReplyKeyboardMarkup(
#         keybord=[
#             [
#                 KeyboardButton(text='Добавить телефон'),
#                 KeyboardButton(text='Отказаться')
#             ]
#         ],
#         resize_keyboard=True
#     )
#     return markup


# def address_keyboard():
#     markup = ReplyKeyboardMarkup(
#         keybord=[
#             [
#                 KeyboardButton(text='Добавить адрес'),
#                 KeyboardButton(text='Отказаться')
#             ]
#         ],
#         resize_keyboard=True
#     )
#     return markup


# def registration_keyboard():
#     markup = ReplyKeyboardMarkup(
#         keyboard=[
#             [
#                 KeyboardButton(text='Согласиться'),
#                 KeyboardButton(text='Отказаться'),
#             ]
#         ],
#         resize_keyboard=True
#     )
#     return markup


# def order_cake_keyboard():
#     markup = ReplyKeyboardMarkup(
#         keyboard=[
#             [
#                 KeyboardButton(text='Заказать торт'),
#                 KeyboardButton(text='Отменить заказ (в главное меню)'),
#             ]
#         ],
#         resize_keyboard=True
#     )
#     return markup


# # Cake composition
# def layers_keyboard():
#     markup = ReplyKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 KeyboardButton(text='1 уровень (+400р)'),
#                 KeyboardButton(text='2 уровня (+750р)'),
#                 KeyboardButton(text='3 уровня (+1100р)'),
#             ],
#             [
#                 KeyboardButton(text='Отменить заказ (в главное меню)'),
#             ]
#         ]
#     )
#     return markup


# def form_keyboard():
#     markup = ReplyKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 KeyboardButton(text='Квадрат (+600)'),
#                 KeyboardButton(text='Круг (+400)'),
#                 KeyboardButton(text='Прямоугольник (+1000)'),
#             ],
#             [
#                 KeyboardButton(text='Отменить заказ (в главное меню)'),
#             ]
#         ]
#     )
#     return markup


# def topping_keyboard():
#     markup = ReplyKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 KeyboardButton(text='Без топпинга (+0)'),
#                 KeyboardButton(text='Белый соус (+200)'),
#                 KeyboardButton(text='Карамельный сироп (+180)'),
#             ],
#             [
#                 KeyboardButton(text='Клубничный сироп (+300)'),
#                 KeyboardButton(text='Черничный сироп (+350)'),
#                 KeyboardButton(text='Молочный шоколад (+200)'),
#             ],
#             [
#                 KeyboardButton(text='Отменить заказ (в главное меню)'),
#             ]
#         ]
#     )
#     return markup


# def berry_keyboard():
#     markup = ReplyKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 KeyboardButton(text='Ежевика (+400)'),
#                 KeyboardButton(text='Малина (+300)'),
#                 KeyboardButton(text='Голубика (+450)'),
#             ],
#             [
#                 KeyboardButton(text='Клубника (+500)'),
#                 KeyboardButton(text='Отменить заказ (в главное меню)'),
#             ]
#         ]
#     )
#     return markup


# def decor_keyboard():
#     markup = ReplyKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 KeyboardButton(text='Фисташки (+300)'),
#                 KeyboardButton(text='Безе (+400)'),
#                 KeyboardButton(text='Фундук (+350)'),
#             ],
#             [
#                 KeyboardButton(text='Пекан (+300)'),
#                 KeyboardButton(text='Маршмеллоу (+200)'),
#                 KeyboardButton(text='Фундук (+300)'),
#             ],
#             [
#                 KeyboardButton(text='Марципан (+280)'),
#                 KeyboardButton(text='Без декора'),
#                 KeyboardButton(text='Отменить заказ (в главное меню)'),
#             ]
#         ]
#     )
#     return markup


# def lettering_keyboard():
#     markup = ReplyKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 KeyboardButton(text='Инпут ввода (+500)'),
#             ],
#             [
#                 KeyboardButton(text='Отменить заказ (в главное меню)'),
#             ]
#         ]
#     )
#     return markup


def get_client_entry(chat_id, tg_user):
    client, is_new = Client.objects.get_or_create(tg_chat_id=chat_id)
    if is_new:
        client.first_name = tg_user.first_name
        client.last_name = tg_user.last_name
        client.save()
    logger.debug(f'Get client from DB: {client}, {is_new}')
    return client


def start(update, context):
    user = update.effective_user
    user_account = get_client_entry(update.message.chat_id, user)
    update.message.reply_text(
        text=f'Привет, {user.first_name}!',
        # reply_markup=get_start_keyboard_markup()
    )
    return States.WHAITING_CLICK


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


# user registration
# def registration_handler(update: Update, context: CallbackContext):
#     chat_id = update.effective_chat.id
#     context.bot.send_message(
#         chat_id=chat_id,
#         text='Ознакомьтесь с политикой по обработке персональных данных.',
#         reply_markup=registration_keyboard()
#     )
#     with open("files/personal_data_policy.pdf", 'rb') as file:
#         context.bot.send_document(chat_id=chat_id, document=file)
#     return WHAITING_CLICK


# def user_registration_db(update):
#     pass


# def agreement_handler(update, context):
#     user_answer = update.effective_message.text
#     chat_id = update.effective_chat.id
#     if user_answer == 'Согласиться':
#         context.bot.send_message(
#             chat_id=chat_id,
#             text='Добавьте свой номер телефона.',
#             reply_markup=contact_keyboard(),
#         )
#         return WHAITING_CLICK

#     if user_answer == 'Отказаться':
#         context.bot.send_message(
#             chat_id=chat_id,
#             text='Очень жаль, что вы отказались от регистрации :(('
#                  'Возвращайтесь!',
#             reply_markup=main_keyboard(chat_id),
#         )
#         return WHAITING_CLICK


# def add_phone_handler(update, context):
#     chat_id = update.effective_chat.id
#     user_answer = update.effective_message.text
#     if user_answer.isdigit():
#         context.bot.send_message(
#             chat_id=chat_id,
#             text='Добавьте адрес доставки.',
#             reply_markup=contact_keyboard()
#         )
#     else:
#         context.bot.send_message(
#             chat_id=chat_id,
#             text='Номер телефона имеет не верный формат.'
#                  'Номер телефона должен состоять только из цифр.',
#             reply_markup=contact_keyboard()
#         )
#     return WHAITING_CLICK


# def add_address_handler(update, context):
#     chat_id = update.effective_chat.id
#     context.bot.send_message(
#         chat_id=chat_id,
#         text='Адрес добавлен!'
#              'Вы можете заказать торт.',
#         reply_markup=order_cake_keyboard()
#     )
#     return LAYERS


# Place an order or redirect the main menu
# def cake_layers_handler(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         'Выберите количество уровней торта',
#         reply_markup=layers_keyboard()
#     )
#     return FORM


# def cake_form_handler(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         'Выберите форму торта',
#         reply_markup=form_keyboard()
#     )
#     return TOPPING


# def cake_topping_handler(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         'Выберите топпинг',
#         reply_markup=topping_keyboard()
#     )
#     return DECOR


# def cake_decor_handler(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         'Выберите декор',
#         reply_markup=decor_keyboard()
#     )
#     return BERRIES


# def cake_berry_handler(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         'Выберите ягоды.',
#         reply_markup=berry_keyboard()
#     )
#     return LETTERING


# def cake_lettering_handler(update: Update, context: CallbackContext):
#     update.message.reply_text(
#         'Мы можем разместить на торте любую надпись.'
#         'Например: «С днем рождения!»',
#         reply_markup=lettering_keyboard()
#     )
#     return ADDRESS


# def order_address_handler(update, context):
#     update.message.reply_text(
#         'Добавьте адрес доставки',
#         reply_markup=order_cake_keyboard()
#     )
#     return ADDRESS


# def cancel_registration_handler(update, context):
#     chat_id = update.effective_chat.id
#     context.bot.send_message(
#         chat_id=chat_id,
#         text='Вы отказались от регистрации :(('
#              'Необходимо согласие на обработку ПД!',
#         reply_markup=main_keyboard(chat_id)
#     )
#     return ConversationHandler.END


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
        entry_points=[CommandHandler('start', start)],
        states={
            States.WHAITING_CLICK: [
                # MessageHandler(
                #     Filters.regex('^Регистрация$'),
                #     registration_handler,
                # ),
                # MessageHandler(
                #     Filters.regex('^Добавить телефон$'),
                #     add_phone_handler
                # ),
                # MessageHandler(
                #     Filters.regex('^Добавить адрес$'),
                #     add_address_handler,
                # ),
            ],
            # LAYERS: [
            #     MessageHandler(
            #         Filters.regex('^1 уровень (+400р)$'),
            #         callback=cake_layers_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^2 уровня (+750р)$'),
            #         callback=cake_layers_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^3 уровня (+1100р)$'),
            #         callback=cake_layers_handler,
            #         pass_user_data=True
            #     ),
            # ],
            # FORM: [
            #     MessageHandler(
            #         Filters.regex('^Квадрат (+600)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Круг (+400)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Прямоугольник (+1000)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            # ],
            # TOPPING: [
            #     MessageHandler(
            #         Filters.regex('^Без топпинга (+0)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Белый соус (+200)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Карамельный сироп (+180)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Кленовый сироп (+200)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Клубничный сироп (+300)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Черничный сироп (+350)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Молочный шоколад (+200)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            # ],
            # BERRIES: [
            #     MessageHandler(
            #         Filters.regex('^Ежевика (+400)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Малина (+300)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Голубика (+450)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Клубника (+500)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            # ],
            # DECOR: [
            #     MessageHandler(
            #         Filters.regex('^Фисташки (+300)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Безе (+400)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Фундук (+350)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Пекан (+300)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Маршмеллоу (+200)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Фундук (+300)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Марципан (+280)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Без декора$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),

            # ],
            # LETTERING: [
            #     MessageHandler(
            #         Filters.regex('^Инпут ввода (+500)$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            #     MessageHandler(
            #         Filters.regex('^Без надписи$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            # ],
            # ADDRESS: [
            #     MessageHandler(
            #         Filters.regex('^Добавить адрес доставки$'),
            #         callback=cake_form_handler,
            #         pass_user_data=True
            #     ),
            # ]
        },
        fallbacks=[
            MessageHandler(Filters.text, cancel_handler)

        ],
    )

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Dialogue system for ordering a cake
    dispatcher.add_handler(conv_handler)

    # on non command i.e message - echo the message on Telegram
    # dispatcher.add_handler(
    #     MessageHandler(
    #         Filters.text & ~Filters.command,
    #         echo
    #     )
    # )

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
