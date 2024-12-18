from aiogram.types import (InlineKeyboardMarkup,
                            InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo)
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import base64


async def start_menu():
    button1 = KeyboardButton(text="Создать розыгрыш")
    button2 = KeyboardButton(text='Мои розыгрыши')
    button3 = KeyboardButton(text='Мои каналы')
    button4 = KeyboardButton(text='Техническая поддержка')
    button5 = KeyboardButton(text='Поддержать бота')
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [button1, button2],
        [button3, button4],
        [button5]
        ], resize_keyboard=True)
    return keyboard

async def channels_list(channels):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="➕ Добавить новый канал", callback_data='add_channel'))
    for channel in channels:
        keyboard.row(InlineKeyboardButton(text=f"{channel[0]}", callback_data=f"channel_{channel[1]}"))
    return keyboard.adjust(1).as_markup()

cancel = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="cancel")]])


async def channel_menu(channel_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Обновить имя", callback_data=f"update_channelName_{channel_id}"))
    keyboard.row(InlineKeyboardButton(text="Удалить из бота", callback_data=f"delete_channel_{channel_id}"))
    return keyboard.adjust(1).as_markup()

async def participation_button_title():
    keyboard = InlineKeyboardBuilder()
    for variant in ["Участвую!", "Участвовать", "Принять участие"]:
        keyboard.row(InlineKeyboardButton(text=variant, callback_data=f"participationTitle_{variant}"))
    return keyboard.adjust(1).as_markup()

lot_without_requirements = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Розыгрыш без обязательных подписок", callback_data="end_requirements")]])

enough_requirements = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Достаточно каналов, идём дальше", callback_data="end_requirements")]])

async def choose_channel_to_lot(channels):
    keyboard = InlineKeyboardBuilder()
    for channel in channels:
        keyboard.row(InlineKeyboardButton(text=f"{channel[0]}", callback_data=f"chooseLotsChannel_{channel[1]}"))
    return keyboard.adjust(1).as_markup()

choose_lot_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Прямо сейчас", callback_data="lotTime_now")],
    [InlineKeyboardButton(text="Запланировать публикацию", callback_data="lotTime_plan")]
    ])

ways_to_end_lot = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="По времени", callback_data="wayToEnd_time")],
    [InlineKeyboardButton(text="По кол-ву участников", callback_data="wayToEnd_count")]
    ])

async def lot_kb(text, lot_id, isInChannel):
    keyboard = InlineKeyboardBuilder()
    
    if not isInChannel:
        keyboard.row(InlineKeyboardButton(text=text))
    else:


        keyboard.row(InlineKeyboardButton(text=text, url=f"t.me/orfo_bot_bot/lot2app?startapp={lot_id}"))
    return keyboard.adjust(1).as_markup()


async def final_lot_checkout(id):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Сохранить розыгрыш", callback_data=f"saveLot_{id}"))
    keyboard.row(InlineKeyboardButton(text="Отмена", callback_data="cancel"))
    return keyboard.adjust(1).as_markup()


