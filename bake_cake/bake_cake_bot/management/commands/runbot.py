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
from textwrap import dedent

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class States(Enum):
    AUTHORIZATION = 0
    LAYERS = 1
    FORM = 2
    TOPPING = 3
    BERRIES = 4
    DECOR = 5
    LETTERING = 6
    ADDRESS = 7
    CLIENT_MAIN_MENU = 8
    INPUT_PHONE = 9
    INPUT_ADDRESS = 10


# Dialogue keyboards
def main_menu_keyboard(show_orders=False):
    keyboard = [
        [KeyboardButton(text='Собрать торт')],
    ]
    if show_orders:
        keyboard.append([KeyboardButton(text='Ваши заказы')])
    logger.info(f'{show_orders} {keyboard}')
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


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


# Function to get or post data to DB
def get_client_entry(chat_id, tg_user):
    client, is_new = Client.objects.get_or_create(tg_chat_id=chat_id)
    logger.info(f'Get client from DB: {client}, {is_new}')
    
    if is_new:
        client.first_name = tg_user.first_name
        client.last_name = tg_user.last_name
        client.save()
    
    return client


def add_phone_to_client(chat_id, phone):
    client, is_new = Client.objects.get_or_create(tg_chat_id=chat_id)
    client.phone = phone
    client.save()
    return client


def add_address_to_client(chat_id, address):
    client, is_new = Client.objects.get_or_create(tg_chat_id=chat_id)
    client.address = address
    client.save()
    return client


# Functions to saend user standard messages
def request_for_input_phone(update):
    logger.info('No phone in DB')
    update.message.reply_text(
        text='Пожалуйста, укажите номер телефона'
    ) 
    return States.INPUT_PHONE 


def request_for_input_address(update):
    logger.info('No address in DB')
    update.message.reply_text(
        text='Пожалуйста, укажите адрес доставки') 
    return States.INPUT_ADDRESS


def send_greeting(client, update):
    is_any_order = client.orders.exists()
    logger.info(f'CLient {client} has orders? {is_any_order}')
    update.message.reply_text(
        text='Добро пожаловать в BakeCake!',
        reply_markup=main_menu_keyboard(is_any_order)
    )    
    return States.CLIENT_MAIN_MENU


# States handlers
def handle_authorization(update, context):
    user = update.effective_user
    client = get_client_entry(update.message.chat_id, user)
    
    if not(client.phone):
        return request_for_input_phone
    
    if not(client.address):
        return request_for_input_address
    
    return send_greeting(client, update)


def handle_phone_input(update, context):
    client = add_phone_to_client(update.message.chat_id, update.message.text)
    
    update.message.reply_text(
        f'В профиль добавлен телефон для связи: {client.phone}',
    )
    logger.info(f'Add phone {client.phone} for {client.tg_chat_id}')

    if not client.address:
        logger.info('No address in DB')
        update.message.reply_text(
            text='Пожалуйста, укажите адрес доставки') 
        return States.INPUT_ADDRESS

    return send_greeting(client, update)


def handle_address_input(update, context):
    client = add_address_to_client(update.message.chat_id, update.message.text) 
    logger.info(f'Add address {client.address} for {client.tg_chat_id}')
    update.message.reply_text(
        f'В профиль добавлен адрес доставки: {client.address}',
    )

    return send_greeting(client, update)


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
#     return AUTHORIZATION


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
#         return AUTHORIZATION

#     if user_answer == 'Отказаться':
#         context.bot.send_message(
#             chat_id=chat_id,
#             text='Очень жаль, что вы отказались от регистрации :(('
#                  'Возвращайтесь!',
#             reply_markup=main_keyboard(chat_id),
#         )
#         return AUTHORIZATION


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
#     return AUTHORIZATION


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

def start(update, context):
    user = update.effective_user
    update.message.reply_text(
        text=f'Привет, {user.first_name}!',
    )
    return handle_authorization(update, context)


def cancel_handler(update, context):
    update.message.reply_text(
        'Очень жаль, что вы отменили заказ :((. Возвращайтесь!'
    )
    return ConversationHandler.END


def help_command(update, context) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


def run_bot(tg_token) -> None:
    updater = Updater(tg_token)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.INPUT_PHONE: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    handle_phone_input
                ),
            ],
            States.INPUT_ADDRESS: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    handle_address_input
                ),
            ],
            States.CLIENT_MAIN_MENU: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    echo
                ),
            ],
        },
        fallbacks=[
            MessageHandler(Filters.text, cancel_handler)
        ],
    )

    dispatcher.add_handler(conv_handler)
    
    dispatcher.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    updater.idle()


class Command(BaseCommand):
    help = 'Import module with telegram bot code'

    def handle(self, *args, **options):
        run_bot(settings.TG_TOKEN)
