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

from telegram import Update
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackContext, ConversationHandler

from django.core.management.base import BaseCommand
from django.conf import settings

from bake_cake_bot.models import Cake, Category, Client, Order, Option
from enum import Enum
from textwrap import dedent

import phonenumbers


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

_option_categories = None
_category_index = None
_current_cake_id = None
_current_order_id = None


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
    ORDER_DETAILS = 11
    CREATE_CAKE = 12
    FINISH_CAKE = 13
    ORDERING = 14
    CHANGE_PHONE = 15
    CHANGE_ADDRESS = 16
    CONSENT_PROCESSING = 17


def parse_order_id(input_string):
    words = input_string.split(' ')
    order_id = [word for word in words if '№' in word][0]
    return int(order_id[1:])


def parse_option_id(input_string):
    words = input_string.split(' ')
    option_id = [word for word in words if '#' in word][0]
    return int(option_id[1:])


# Dialogue keyboards
def create_main_menu_keyboard(show_orders=False):
    keyboard = [
        [KeyboardButton(text='Собрать торт')],
    ]
    if show_orders:
        keyboard.append([KeyboardButton(text='Ваши заказы')])
    logger.info(f'{show_orders} {keyboard}')
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def create_orders_keyboard(orders):
    keyboard = []
    text_template = 'Заказ №{id} на сумму {total_amount} от {created_at}'
    for order in orders:
        keyboard.append(
            [KeyboardButton(text=text_template.format(
                id=order.id,
                total_amount=order.total_amount,
                created_at=order.created_at,
            ))
            ],
        )
    keyboard.append(
        [KeyboardButton(text='В главное меню')],
    )
    logger.info(f'Create orders keyboard {keyboard}')
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def create_options_keyboard(category):
    keyboard = []

    if not category.is_mandatory:
        keyboard.append([KeyboardButton(text='Пропустить')])

    text_template = '{name} + {price} руб. #{option_id}'

    options = category.options.all()
    logger.info(f'Категория {category}: {options}')

    for option in options:
        keyboard.append(
            [KeyboardButton(text=text_template.format(
                name=option.name,
                price=option.price,
                option_id=option.id,
            ))
            ],
        )

    keyboard.append(
        [KeyboardButton(text='В главное меню')],
    )
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def create_to_order_keyboard():
    keyboard = [
        [KeyboardButton(text='Оформить заказ')],
        [KeyboardButton(text='В главное меню')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def create_order_comfirm_keyboard():
    keyboard = [
        [KeyboardButton(text='Подтвердить заказ')],
        [KeyboardButton(text='Изменить телефон')],
        [KeyboardButton(text='Изменить адрес')],
        [KeyboardButton(text='Отменить')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def accept_consent_processing():
    keyboard = [
        [KeyboardButton(text='Принять соглашение')],
        [KeyboardButton(text='Отказаться')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# Function to get or post data to DB
def create_new_order(cake_id, chat_id):
    cake = Cake.objects.get(id=cake_id)
    client = Client.objects.get(tg_chat_id=chat_id)

    order = Order.objects.create(
        client=client,
    )
    order.cakes.set([cake])
    order.save()

    cake.is_in_order = True
    cake.save()
    return order


def get_client_entry(chat_id, tg_user):
    client, is_new = Client.objects.get_or_create(tg_chat_id=chat_id)
    logger.info(f'Get client from DB: {client}, {is_new}')

    if is_new:
        client.first_name = tg_user.first_name
        logger.info(f'Last name: {tg_user.last_name}, {bool(tg_user.last_name)}')
        if tg_user.last_name:
            client.last_name = tg_user.last_name
        client.save()

    return client


def add_consent_processing(chat_id, consest):
    client, is_new = Client.objects.get_or_create(tg_chat_id=chat_id)
    client.pd_proccessing_consent = consest
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


def get_client_orders(chat_id):
    client = Client.objects.get(tg_chat_id=chat_id)
    orders = client.orders.all()
    logger.info(f'Get orders: {orders}')
    return orders


def get_order_details(order_id):
    order = (
        Order.objects
        .select_related('client')
        .prefetch_related('cakes')
        .get(id=order_id)
    )
    return order


def load_categories():
    return Category.objects.prefetch_related('options').order_by('choice_order')


def create_new_cake(chat_id):
    cake = Cake.objects.create(
        created_by=Client.objects.get(tg_chat_id=chat_id),
    )
    return cake.id


def add_option_to_cake(option_id, cake_id):
    cake = Cake.objects.get(id=cake_id)
    option = Option.objects.get(id=option_id)
    cake.options.add(option)
    cake.save()
    return cake


def delete_cake(cake_id):
    Cake.objects.get(id=cake_id).delete()
    return


def request_consent_processing(update, context, chat_id):
    with open("files/personal_data_policy.pdf", 'rb') as file:
        context.bot.send_document(chat_id=chat_id, document=file)
    update.message.reply_text(
        text='Пожалуйста, дайте согласине на обработку персональных данных',
        reply_markup=accept_consent_processing()
    )
    return States.CONSENT_PROCESSING


# Functions to send user standard messages
def request_for_input_phone(update):
    logger.info('No phone in DB')
    update.message.reply_text(
        text='Пожалуйста, укажите номер телефона',
        reply_markup=ReplyKeyboardRemove()
    )
    return States.INPUT_PHONE


def request_for_input_address(update):
    logger.info('No address in DB')
    update.message.reply_text(
        text='Пожалуйста, укажите адрес доставки'
    )
    return States.INPUT_ADDRESS


def invite_user_to_main_menu(update):
    client = Client.objects.get(tg_chat_id=update.message.chat_id)
    is_any_order = client.orders.exists()
    logger.info(f'CLient {client} has orders? {is_any_order}')
    update.message.reply_text(
        text='Выберите действие',
        reply_markup=create_main_menu_keyboard(is_any_order)
    )
    return States.CLIENT_MAIN_MENU


def send_option_choices(update, category):
    update.message.reply_text(
        text=f'Выберите вариант "{category.title}"',
        reply_markup=create_options_keyboard(category)
    )
    return


def get_next_category(update, category_number):

    global _category_index
    _category_index += 1

    logger.info(f'Next {_category_index}/{len(_option_categories)}')

    if _category_index >= len(_option_categories):
        invite_to_ordering(update)
        return States.FINISH_CAKE

    send_option_choices(update, _option_categories[_category_index])
    return States.CREATE_CAKE


def invite_to_ordering(update):
    global _category_index
    global _current_cake_id

    _category_index = None
    logger.info('Options has been chosen')

    update.message.reply_text(
        text='Торт готов!',
        reply_markup=create_to_order_keyboard()
    )
    return


def send_order_info(update, order):
    orders_states = dict(order.get_order_states())
    logger.info(f'States {orders_states}')
    update.message.reply_text(dedent(f'''\
        Заказ №{order.id}
        Статус заказа: {orders_states[order.status]}

        Количество тортов в заказе: {order.cakes.count()}
        Стоимость заказа: {order.total_amount}

        Имя получателя: {order.client.first_name} {order.client.last_name}
        Телефон: {order.client.phone}
        Адрес доставки: {order.client.address}'''))
    return


def invite_to_confirm_order(update, order):
    send_order_info(update, order)
    update.message.reply_text(
        text='Проверьте свой заказ',
        reply_markup=create_order_comfirm_keyboard()
    )
    return


# States handlers
def handle_return_to_menu(update, context):
    global _category_index
    global _current_cake_id

    logger.info(f'Delete cake {_current_cake_id}')
    if _current_cake_id:
        logger.info(f'Delete cake {_current_cake_id}')
        delete_cake(_current_cake_id)
    _category_index = None
    _current_cake_id = None

    user = update.effective_user
    client = get_client_entry(update.message.chat_id, user)
    return invite_user_to_main_menu(update)


def handle_authorization(update, context):
    user = update.effective_user
    chat_id = update.message.chat_id
    client = get_client_entry(chat_id, user)

    if not(client.pd_proccessing_consent):
        return request_consent_processing(update, context, chat_id)

    if not(client.phone):
        return request_for_input_phone(update)

    if not(client.address):
        return request_for_input_address(update)

    return invite_user_to_main_menu(update)


def handle_consent_processing(update, context):
    client_input = update.message.text
    if client_input == 'Принять соглашение':
        consent_processing = True
    elif client_input == 'Отказаться':
        consent_processing = False
    else:
        return handle_not_understand(update)

    client = add_consent_processing(update.message.chat_id, consent_processing)

    update.message.reply_text(
        text='Вы согласились на обработку персональных данных'
    )
    # Возвращаем авторизацию, чтобы заполнить недостающие данные
    return handle_authorization(update, context)


def handle_phone_input(update, context):
    if not phonenumbers.is_valid_number(
        phonenumbers.parse(
            update.message.text,
            "RU"
        )
    ):
        update.message.reply_text(
            text='Введите корректрый номер телефона'
        )
        return States.INPUT_PHONE

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

    return invite_user_to_main_menu(update)


def handle_address_input(update, context):
    client = add_address_to_client(update.message.chat_id, update.message.text)
    logger.info(f'Add address {client.address} for {client.tg_chat_id}')
    update.message.reply_text(
        f'В профиль добавлен адрес доставки: {client.address}',
    )

    return invite_user_to_main_menu(update)


def handle_show_orders(update, context):
    orders = get_client_orders(update.message.chat_id)

    reply_markup = create_orders_keyboard(orders)

    update.message.reply_text(
        'Выберите заказ для просмотра',
        reply_markup=reply_markup
    )
    return States.ORDER_DETAILS


def handle_order_details(update, context):
    order_id = parse_order_id(update.message.text)
    logger.info(f'Parse order id: {order_id}')
    order = get_order_details(order_id)

    send_order_info(update, order)
    return States.ORDER_DETAILS


def handle_create_cake(update, context):
    global _option_categories
    global _category_index
    global _current_cake_id

    if _category_index is None:
        # Подгружаем категории и создаем клавиатуру
        _option_categories = list(load_categories())
        print(_option_categories)
        _category_index = 0
        _current_cake_id = create_new_cake(update.message.chat_id)
        send_option_choices(update, _option_categories[_category_index])
        logger.info(f'Send {_category_index}/{len(_option_categories)}')
        return States.CREATE_CAKE

    option_id = parse_option_id(update.message.text)
    add_option_to_cake(option_id, _current_cake_id)
    logger.info(f'Add option {option_id} to cake {_current_cake_id}')

    return get_next_category(update, len(_option_categories))


def handle_skip_option(update, context):
    global _option_categories
    return get_next_category(update, len(_option_categories))


def handle_finish_cake(update, context):
    update.message.reply_text(
        text='Торт готов!',
    )
    return States.FINISH_CAKE


def handle_create_order(update, context):
    global _current_cake_id
    global _current_order_id

    order = create_new_order(_current_cake_id, update.message.chat_id)
    _current_cake_id = None

    invite_to_confirm_order(update, order)

    _current_order_id = order.id
    return States.ORDERING


def handle_confirm_order(update, context):
    global _current_order_id

    order = Order.objects.get(id=_current_order_id)
    order.status = 1
    order.save()

    update.message.reply_text(
        text=f'Заказ № {_current_order_id} подтвержден'
    )
    _current_order_id = None
    return invite_user_to_main_menu(update)


def handle_request_other_address(update, context):
    update.message.reply_text(
        text='Введите адрес доставки'
    )
    return States.CHANGE_ADDRESS


def handle_request_other_phone(update, context):
    update.message.reply_text(
        text='Введите номер телефона для связи'
    )
    return States.CHANGE_PHONE


def handle_phone_change(update, context):
    global _current_order_id

    client = add_phone_to_client(update.message.chat_id, update.message.text)

    update.message.reply_text(
        f'В профиль добавлен телефон для связи: {client.phone}',
    )
    logger.info(f'Add phone {client.phone} for {client.tg_chat_id}')

    order = Order.objects.get(id=_current_order_id)
    invite_to_confirm_order(update, order)
    return States.ORDERING


def handle_address_change(update, context):
    client = add_address_to_client(update.message.chat_id, update.message.text)

    update.message.reply_text(
        f'В профиль добавлен адрес доставки: {client.address}',
    )
    logger.info(f'Add address {client.address} for {client.tg_chat_id}')

    order = Order.objects.get(id=_current_order_id)
    invite_to_confirm_order(update, order)
    return States.ORDERING


def start(update, context):
    user = update.effective_user
    update.message.reply_text(
        text=f'Привет, {user.first_name}!',
    )
    return handle_authorization(update, context)


def handle_not_understand(update):
    update.message.reply_text(
        text='Извините, но я вас не понял :(',
    )


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
            States.CONSENT_PROCESSING: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    handle_consent_processing
                ),
            ],
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
                    Filters.regex('^Ваши заказы$'),
                    handle_show_orders
                ),
                MessageHandler(
                    Filters.regex('^Собрать торт$'),
                    handle_create_cake
                ),
            ],
            States.CREATE_CAKE: [
                MessageHandler(
                    Filters.regex('^Пропустить$'),
                    handle_skip_option,
                ),
                MessageHandler(
                    Filters.regex('^В главное меню$'),
                    handle_return_to_menu,
                ),
                MessageHandler(
                    Filters.regex('руб. #'),
                    handle_create_cake
                ),
            ],
            States.FINISH_CAKE: [
                MessageHandler(
                    Filters.regex('^В главное меню$'),
                    handle_return_to_menu,
                ),
                MessageHandler(
                    Filters.regex('^Оформить заказ$'),
                    handle_create_order,
                ),
            ],
            States.ORDERING: [
                MessageHandler(
                    Filters.regex('^Подтвердить заказ$'),
                    handle_confirm_order,
                ),
                MessageHandler(
                    Filters.regex('^Изменить адрес$'),
                    handle_request_other_address,
                ),
                MessageHandler(
                    Filters.regex('^Изменить телефон$'),
                    handle_request_other_phone,
                ),
                MessageHandler(
                    Filters.regex('^Отменить$'),
                    handle_return_to_menu,
                ),
            ],
            States.CHANGE_PHONE: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    handle_phone_change
                ),
            ],
            States.CHANGE_ADDRESS: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    handle_address_change
                ),
            ],
            States.ORDER_DETAILS: [
                MessageHandler(
                    Filters.regex('^В главное меню$'),
                    handle_return_to_menu,
                ),
                MessageHandler(
                    Filters.regex('^Заказ №*'),
                    handle_order_details,
                ),
            ]
        },
        fallbacks=[
            MessageHandler(
                Filters.text & ~Filters.command,
                handle_not_understand
            )
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
