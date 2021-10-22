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

from bake_cake_bot.models import Cake, Category, Client, Order, Option
from enum import Enum
from textwrap import dedent

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

_option_categories = None
_category_index = None
_current_cake_id = None


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

    text_template = '{name} +{price} руб. #{option_id}'

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


# Functions to send user standard messages
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


def invite_user_to_main_menu(client, update):
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


def invite_to_confirm_order(update):
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
    return invite_user_to_main_menu(client, update)


def handle_authorization(update, context):
    user = update.effective_user
    client = get_client_entry(update.message.chat_id, user)
    
    if not(client.phone):
        return request_for_input_phone(update)
    
    if not(client.address):
        return request_for_input_address(update)
    
    return invite_user_to_main_menu(client, update)


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

    return invite_user_to_main_menu(client, update)


def handle_address_input(update, context):
    client = add_address_to_client(update.message.chat_id, update.message.text) 
    logger.info(f'Add address {client.address} for {client.tg_chat_id}')
    update.message.reply_text(
        f'В профиль добавлен адрес доставки: {client.address}',
    )

    return invite_user_to_main_menu(client, update)


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

    order = create_new_order(_current_cake_id, update.message.chat_id)
    _current_cake_id = None

    send_order_info(update, order)
    invite_to_confirm_order(update)
    return States.ORDERING


def handle_confirm_order(update, context):
    pass   
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


# Place an order or redirect the main menu

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
                    Filters.regex('^Подтвердить$'),
                    handle_confirm_order,
                ),
                MessageHandler(
                    Filters.regex('^Отменить$'),
                    handle_return_to_menu,
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
            MessageHandler(Filters.text & ~Filters.command, cancel_handler)
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
