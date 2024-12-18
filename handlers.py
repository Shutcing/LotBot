from contextlib import suppress

from aiogram import F, Router
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER, ADMINISTRATOR
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
import asyncio
from datetime import datetime

import fsm
from datetime import datetime, timedelta
import keyboards as kb
from db_connect import Database
from user import User
from fsm import NewChannelState, NewLotState, ParticipationButtonTitleState, RequiredChannelState, WinnersCountState, LotDateState,LotEndDateState, LotEndCountState

ROUTER = Router()
ROUTER.my_chat_member.filter(F.chat.type.in_({"group", "supergroup", "channel"}))
DB = Database("sqlite:///new_db.db")
ID = 0
LOTS = {}

def get_add_channel_instruction(name):
    return f'''
        Инструкция

        Добавьте бота (@{name}) в ваш канал или чат как администратора с правом публикации сообщений. После этого отправьте мне канал в формате @channelname. Если вы хотите добавить приватный канал перешлите из него сообщение, или скопируйте и пришлите боту ссылку на любое сообщение из приватного канала.

        ⚠️ Если вы хотите использовать бота в группе (чате), обязательно выдайте ему право писать в ней.
        '''

def get_make_lot_instruction(name):
    return f'''
    Создание розыгрыша

    ✉️ Отправьте текст для розыгрыша. Вы можете также отправить вместе с текстом картинку, видео или GIF, пользоваться разметкой.
    ❗️ Вы можете использовать только 1 медиафайл

    Бот для проведения конкурсов полностью бесплатный, прозрачный и без рекламы, ему будет приятно, если в конкурсном посте Вы укажите на него ссылку, спасибо. @{name}
    '''

def get_make_lot_requirement_instruction(name):
    return f'''
    📊 Добавьте каналы, на которые пользователям нужно будет подписаться для участия в розыгрыше.
    Подписка на канал, в котором проводится розыгрыш, обязательна и включена по умолчанию.

    Чтобы добавить канал, нужно:
    1. Добавить бота (@{name}) в ваш канал как администратора (это нужно, чтобы бот мог проверить подписан ли пользователь на канал).
    2. Отправить боту канал в формате @channelname (или переслать сообщение из канала).

    ⚠️ Если вы хотите чтобы участвовать в розыгрыше можно было без подписок на канал, нажмите кнопку ниже:
    '''

def get_add_new_required_channel_answer():
    return '''
    ✅ Канал добавлен, вы можете добавить еще один (просто продолжайте присылать каналы) или продолжить создание розыгрыша:

    Не забирайте у бота права администратора канала, иначе проверка подписки происходить не будет!
    '''


async def success_add_channel_reaction(id):
    text = """
    ✅ Канал Канал добавлен, можно переходить к созданию розыгрыша!

    Чтобы создать новый розыгрыш, введите команду /new_lot
    """
    await ROUTER.bot.send_message(
            chat_id=id,
            text=text)
    

async def get_channel_inf(username: str):
    try:
        chat = await ROUTER.bot.get_chat(username)
        return chat
    except Exception as e:
        print(f"Ошибка: {e}")
        return None
    

async def is_bot_admin(channel_id: int):
    try:
        chat_member = await ROUTER.bot.get_chat_member(chat_id=channel_id, user_id=(await ROUTER.bot.get_me()).id)
        return chat_member.status == "administrator"
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    
def extract_media_and_text(message: Message):
    result = {}
    if message.photo:
        # Извлекаем file_id последней (самой большой) картинки
        result["file"] = message.photo[-1].file_id
    elif message.animation:
        result["file"] = message.animation.file_id
    if message.text:
        result["text"] = message.text
    elif message.caption:
        result["text"] = message.caption
    return result

    

async def make_new_lot(message, state):
    if len(DB.get_user_channels(message.from_user.id)) == 0:
        await message.answer('❌ У вас не добавлен ни один канал, чтобы добавить канал в бота, нажмите кнопку "Мои каналы 📢"')
        return
    
    await message.answer(text=get_make_lot_instruction((await ROUTER.bot.get_me()).username), reply_markup = kb.cancel)
    await state.set_state(NewLotState.new_lot)
    DB.set_user_chat_state(message.from_user.id, "new_lot")


async def write_participation_button_title(id, title, state):
    LOTS[id]["participation"] = title
    await ROUTER.bot.send_message(
            chat_id=id,
            text="✅ Текст кнопки сохранен")
    
    await ROUTER.bot.send_message(
            chat_id=id,
            text=get_make_lot_requirement_instruction((await ROUTER.bot.get_me()).username),
            reply_markup=kb.lot_without_requirements)
    
    await state.set_state(RequiredChannelState.required_channel)
    DB.set_user_chat_state(id, "required_channel")


async def choose_lot_date(id, date):
    LOTS[id]["date"] = date
    await ROUTER.bot.send_message(
        chat_id=id,
        text="✅ Время публикации выбрано")
        
    await ROUTER.bot.send_message(
        chat_id=id,
        text="🗓 Как завершить розыгрыш?",
        reply_markup= kb.ways_to_end_lot)

async def choose_lot_end_conditions(id, date_or_count, isDate):
    if isDate:
        LOTS[id]["end_date"] = date_or_count
        await ROUTER.bot.send_message(
            chat_id=id,
            text="✅ Время для подведения результатов сохранено")
    else:
        LOTS[id]["end_count"] = date_or_count
        await ROUTER.bot.send_message(
            chat_id=id,
            text=f"✅ Количество участников для подведения результатов сохранено: {date_or_count}")
        
    if "file" in LOTS[id]:
        await ROUTER.bot.send_photo(id, photo=LOTS[id]["file"], caption=LOTS[id]["text"], reply_markup=await kb.lot_kb(LOTS[id]["participation"], id, False))
    else:
        await ROUTER.bot.send_message(
            chat_id=id,
            text=LOTS[id]["text"],
            reply_markup = await kb.lot_kb(LOTS[id]["participation"], id, False))
        
    await ROUTER.bot.send_message(
            chat_id=id,
            text=make_checkout_lot_text(id, isDate),
            reply_markup = await kb.final_lot_checkout(id))
    

async def send_lot_to_channel(id):
    await ROUTER.bot.send_message(
        chat_id=LOTS[id]["channel_id"],
        text=LOTS[id]["text"],
        reply_markup = await kb.lot_kb(LOTS[id]["participation"], id, True))
    


def make_checkout_lot_text(id, isDate):
    if isDate:
        return  f'''
        🧮 Внимательно перепроверьте розыгрыш

        Розыгрыш завершится {LOTS[id]["end_date"]}
        Количество победителей: {LOTS[id]["winners_count"]}
        '''
    else:
        return f'''
        🧮 Внимательно перепроверьте розыгрыш

        Розыгрыш завершится, когда количество участников станет равно {LOTS[id]["end_count"]}
        Количество победителей: {LOTS[id]["winners_count"]}
        '''
    
        
def make_time_examples():

    now = datetime.now()
    ten_m = now + timedelta(minutes=10) - timedelta(hours=2)
    one_h = now + timedelta(hours=1) - timedelta(hours=2)
    one_d = now + timedelta(days=1) - timedelta(hours=2)
    one_w = now + timedelta(weeks=1) - timedelta(hours=2)

    return f'''
    {ten_m.strftime("%d.%m.%y %H:%M")} - через 10 минут
    {one_h.strftime("%d.%m.%y %H:%M")} - через час
    {one_d.strftime("%d.%m.%y %H:%M")} - через день
    {one_w.strftime("%d.%m.%y %H:%M")} - через неделю
    '''


def isDateCorrect(date):
    try:
        input_date = datetime.strptime(date, '%d.%m.%y %H:%M')
        if input_date > datetime.now() - timedelta(hours=2):
            return True
        else:
            return False
    except ValueError:
        return False

#----Реакции на состояния-----------------------------------------------------
@ROUTER.message(NewChannelState.new_channel)
async def add_channel_by_username(message: Message, state: FSMContext):
    channels_id = [c[1] for c in DB.get_user_channels(message.from_user.id)]
    chat = await get_channel_inf(message.text)
    if chat is None:
        await message.answer("❌ Ошибка: не удается проверить ваши права администратора в канале!")
        await state.clear()
        DB.set_user_chat_state(message.from_user.id, "")
        return 
    
    current_channel_id = chat.id
    current_channel_name = chat.title
    if (await is_bot_admin(current_channel_id)):
        if current_channel_id not in channels_id:
            DB.add_channel(message.from_user.id, current_channel_name, current_channel_id)
            await success_add_channel_reaction(message.from_user.id)
    else:
        await message.answer("❌ Бот не является администратором этого канала")
    await state.clear()
    DB.set_user_chat_state(message.from_user.id, "")


@ROUTER.message(NewLotState.new_lot)
async def write_lot_content(message: Message, state: FSMContext):
    media = extract_media_and_text(message)
    LOTS[message.from_user.id] = {}
    LOTS[message.from_user.id]["text"] = media["text"]
    if "file" in media:
        LOTS[message.from_user.id]["file"] = media["file"]
        await message.answer("✅ Фото добавлено")
    await state.clear()
    DB.set_user_chat_state(message.from_user.id, "")
    await message.answer("✅ Текст добавлен")
    await message.answer(
        text="📰 Отправьте текст, который будет отображаться на кнопке, или выберите один из вариантов кнопкой:",
        reply_markup=await kb.participation_button_title())
    await state.set_state(ParticipationButtonTitleState.participation_button_title)
    DB.set_user_chat_state(message.from_user.id, "participation_button_title")


@ROUTER.message(ParticipationButtonTitleState.participation_button_title)
async def get_custom_participation_button_title(message: Message, state: FSMContext):
    await state.clear()
    DB.set_user_chat_state(message.from_user.id, "")
    await write_participation_button_title(message.from_user.id, message.text, state)

@ROUTER.message(RequiredChannelState.required_channel)
async def get_required_channel_username(message: Message, state: FSMContext):
    r_channel = await get_channel_inf(message.text)
    id = message.from_user.id
    if "requirements" not in LOTS[id]:
        LOTS[id]["requirements"] = set()
    else:
        LOTS[id]["requirements"].add([r_channel.title, r_channel.id])

    await message.answer(text=get_add_new_required_channel_answer(),
                         reply_markup=kb.enough_requirements)
    

@ROUTER.message(WinnersCountState.winners_count)
async def get_winners_count(message: Message, state: FSMContext):
    await state.clear()
    DB.set_user_chat_state(message.from_user.id, "")

    winners_count = int(message.text)
    LOTS[message.from_user.id]["winners_count"] = winners_count

    await ROUTER.bot.send_message(
            chat_id=message.from_user.id,
            text=f"✅ Количество победителей сохранено: {winners_count}")
    
    channels = DB.get_user_channels(message.from_user.id)
    await ROUTER.bot.send_message(
            chat_id=message.from_user.id,
            text=f"🗓 В каком канале публикуем розыгрыш?",
            reply_markup= await kb.choose_channel_to_lot(channels))

@ROUTER.message(LotDateState.lot_date)
async def get_lot_date(message: Message, state: FSMContext):
    if not isDateCorrect(message.text):
        await ROUTER.bot.send_message(
            chat_id=message.from_user.id,
            text="❌ Дата публицации: Неверно указана дата!\nФормат: дд.мм.гг чч:мм")
    else:
        await state.clear()
        DB.set_user_chat_state(message.from_user.id, "")

        await choose_lot_date(message.from_user.id, message.text)


@ROUTER.message(LotEndDateState.lot_end_date)
async def get_lot_end_date(message: Message, state: FSMContext):
    if not isDateCorrect(message.text):
        await ROUTER.bot.send_message(
            chat_id=message.from_user.id,
            text="❌ Дата подведения результатов: Неверно указана дата!\nФормат: дд.мм.гг чч:мм")
    else:
        await state.clear()
        DB.set_user_chat_state(message.from_user.id, "")

        await choose_lot_end_conditions(message.from_user.id, message.text, True)


@ROUTER.message(LotEndCountState.lot_end_count)
async def get_lot_end_count(message: Message, state: FSMContext):
        await state.clear()
        DB.set_user_chat_state(message.from_user.id, "")
        await choose_lot_end_conditions(message.from_user.id, message.text, False)
    
#------сommands--------------------------------------------
@ROUTER.message(CommandStart())
async def cmd_start(message: Message):
    if not DB.user_exists(message.from_user.id):
        DB.add_user(message.from_user.id)
    await message.answer("👋 Приветствуем!\nНаш бот поможет Вам провести розыгрыш на канале.\nГотовы создать новый розыгрыш?", reply_markup=await kb.start_menu())

@ROUTER.message(Command("new_lot"))
async def make_new_lot_command(message: Message, state: FSMContext):
    await make_new_lot(message, state)

#------Start_Menu Commands-----------------------------------------------
@ROUTER.message(lambda message: message.text is not None and "Создать розыгрыш" in message.text)
async def make_new_lot_button(message: Message, state: FSMContext):
    await make_new_lot(message, state)


@ROUTER.message(lambda message: message.text is not None and "Мои каналы" in message.text)
async def show_channels(message: Message):
    channels = DB.get_user_channels(message.from_user.id)
    await message.answer(text="ℹ️ Добавленные вами каналы:", reply_markup=await kb.channels_list(channels))

@ROUTER.message(lambda message: message.text is not None and "/delete_channel" in message.text)
async def delete_channel(message: Message):
    channel_id = int(message.text.split()[-1])
    channels = [c[1] for c in DB.get_user_channels(message.from_user.id)]


    if channel_id in channels:
        DB.delete_channel_by_id(channel_id)
        await message.answer("✅ Канал удален из бота")
    else:
        await message.answer("❌ Вы не являетесь администратором этого канала")
#---Callbacks----------------------------------------------------------------
@ROUTER.callback_query(F.data == "add_channel")
async def send_adding_channel_instruction(callback: CallbackQuery, state: FSMContext):
    global ID
    await state.set_state(NewChannelState.new_channel)
    DB.set_user_chat_state(callback.from_user.id, "new_channel")
    ID = callback.from_user.id
    callback.answer("")
    await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text=get_add_channel_instruction((await ROUTER.bot.get_me()).username),
            reply_markup = kb.cancel
        )
    
@ROUTER.callback_query(lambda F: "delete_channel" in F.data)
async def send_delete_channel_confirmation(callback: CallbackQuery):
    channel_id = int(callback.data.split("_")[-1])
    await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text=f"⚠️ Чтобы удалить канал из бота, введите команду:\n/delete_channel {channel_id}")
    

@ROUTER.callback_query(F.data.split("_")[0] == "channel")
async def send_channel_menu(callback: CallbackQuery):
    channel_id = int(callback.data.split("_")[1])
    await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text="📢 Меню канала:",
            reply_markup = await kb.channel_menu(channel_id))
    


@ROUTER.callback_query(F.data.split("_")[0] == "participationTitle")
async def get_standart_participation_button_title(callback: CallbackQuery, state: FSMContext):
    title = callback.data.split("_")[1]
    await write_participation_button_title(callback.from_user.id, title, state)



@ROUTER.callback_query(F.data == "end_requirements")
async def end_lot_requirements(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    DB.set_user_chat_state(callback.from_user.id, "")

    await ROUTER.bot.send_message(
        chat_id=callback.from_user.id,
        text=f"✅ Сохранено")
    
    await ROUTER.bot.send_message(
        chat_id=callback.from_user.id,
        text=f"🧮 Сколько победителей выбрать боту?")
    
    await state.set_state(WinnersCountState.winners_count)
    DB.set_user_chat_state(callback.from_user.id, "winners_count")


@ROUTER.callback_query(F.data.split("_")[0] == "chooseLotsChannel")
async def choose_lot_channel(callback: CallbackQuery):
    channel_id = int(callback.data.split("_")[1])

    LOTS[callback.from_user.id]["channel_id"] = channel_id

    await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text="✅ Канал выбран")
    await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text="⏰ Когда нужно опубликовать розыгрыш?",
            reply_markup= kb.choose_lot_time)
    

@ROUTER.callback_query(F.data.split("_")[0] == "lotTime")
async def choose_lot_time_by_btns(callback: CallbackQuery, state: FSMContext):
    time_type = callback.data.split("_")[1]

    if time_type == "now":
        await choose_lot_date(callback.from_user.id, (datetime.now() - timedelta(hours=2)).strftime("%d.%m.%y %H:%M") )
    else:    
        await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text="⏰ Когда нужно опубликовать розыгрыш? (Укажите время в формате дд.мм.гг чч:мм)\nБот живет по времени (GMT+3) Москва, Россия")
        await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text=f"Примеры:\n\n{make_time_examples()}")
        
        await state.set_state(LotDateState.lot_date)
        DB.set_user_chat_state(callback.from_user.id, "lot_date")


@ROUTER.callback_query(F.data.split("_")[0] == "wayToEnd")
async def choose_lot_time_by_btns(callback: CallbackQuery, state: FSMContext):
    way = callback.data.split("_")[1]

    if way == "time":
        await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text="🏁 Когда нужно определить победителя? (Укажите время в формате дд.мм.гг чч:мм)\nБот живет по времени (GMT+3) Москва, Россия")
        await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text=f"Примеры:\n\n{make_time_examples()}")
        
        await state.set_state(LotEndDateState.lot_end_date)
        DB.set_user_chat_state(callback.from_user.id, "lot_end_date")
    else:
        await ROUTER.bot.send_message(
            chat_id=callback.from_user.id,
            text='''
            🏁 Укажите количество участников для проведения розыгрыша:

            ❗️ Обратите внимание, участник - тот, кто поучаствовал в конкурсе, выбор будет не по количеству подписчиков канала, а именно по количеству участников (кто нажал на кнопку в конкурсе)")
            ''')
        await state.set_state(LotEndCountState.lot_end_count)
        DB.set_user_chat_state(callback.from_user.id, "lot_end_coun")


@ROUTER.callback_query(F.data.split("_")[0] == "saveLot")
async def save_lot(callback: CallbackQuery, state: FSMContext):
    print("yes")
    print(LOTS[callback.from_user.id]["date"])
    date = datetime.strptime(LOTS[callback.from_user.id]["date"], '%d.%m.%y %H:%M') + timedelta(hours=2)
    if date < datetime.now():
        date = datetime.now() + timedelta(seconds=2)
    
    user_id = callback.from_user.id
    lot_id = len(DB.get_lots_by_user_id(user_id))
    if "file" in LOTS[user_id]:
        file = LOTS[user_id]["file"]
    else:
        file = 0

    if "end_count" in LOTS[user_id]:
        end_count = LOTS[user_id]["end_count"]
    else:
        end_count = -1

    if "end_date" in LOTS[user_id]:
        end_date = LOTS[user_id]["end_date"]
    else:
        end_date = ""
    DB.add_lot(lot_id, user_id, LOTS[user_id]["text"], file, LOTS[user_id]["participation"], LOTS[user_id]["winners_count"], LOTS[user_id]["channel_id"], LOTS[user_id]["date"], end_count, end_date)


    ROUTER.scheduler.add_job(send_lot_to_channel, "date", run_date=date,
                          args=[lot_id])
        

#---Ожидание того, что бота сделают администратором-----------------------------------------------------
@ROUTER.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR))
async def bot_added_as_admin(event: ChatMemberUpdated, state: FSMContext):    
    if DB.get_user_chat_state(ID) == "new_channel":
        await success_add_channel_reaction(ID)
        await state.clear()
        DB.set_user_chat_state(ID, "")
        
        channels_id = [c[1] for c in DB.get_user_channels(ID)]
        if event.chat.id not in channels_id:
            DB.add_channel(ID, event.chat.title, event.chat.id)


    # await event.answer(
    #     text=f"Привет! Спасибо, что добавили меня в "
    #          f'Канал "{event.chat.title}" '
    #          f"как администратора. ID чата: {event.chat.id}"
    # )


#---Обработка неизвестных сообщений---------------------------------------------
@ROUTER.message()
async def process_unknown_command(message: Message):
    await message.answer("Извини, я не знаю такой команды.")
        
