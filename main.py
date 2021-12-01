# -*- coding: utf-8 -*-

import logging
import config
from aiogram import *
from aiogram.types import *
from aiogram.utils.callback_data import CallbackData
import sqlite3 as sq
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from captcha.image import ImageCaptcha
import random
import aiogram.utils.markdown as md
from datetime import *
import pytz
import os 
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.builtin import Text
from aiogram.dispatcher.filters.state import State, StatesGroup, any_state
from aiogram.dispatcher.handler import CancelHandler
from config import TIMEZONE
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import BotBlocked

async def send_error_chat(*args, **kwargs):
    await bot.send_message(config.error, *args, **kwargs)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

answer_live_cb = CallbackData("answer_live", "user_id")
send_commercial_cb = CallbackData("commercial", "user_id")
support_cb = CallbackData("ask_support", "messages", "user_id", "as_user")
cancel_support_callback = CallbackData("cancel_support", "user_id")
cancel_cb = CallbackData("cancel", "step")

ORDER_MESSAGES = {
    "exit": "Скасовано \n\n Щоб повернутись в головне меню 👉 /start",
}

cancel_support = InlineKeyboardMarkup().add(
    InlineKeyboardButton(
        text="❌ Завершити спілкування",
        callback_data="cancel_support",
    )
)

def get_cancel_button(step: str = ""):
    if step == "":
        text = "❌Вихід"
    else:
        text = "◀️ Назад"
    callback = cancel_cb.new(step=step)
    return InlineKeyboardButton(text, callback_data=callback)

@dp.callback_query_handler(cancel_cb.filter(), state=any_state)
async def handle_cancel(call: CallbackQuery, callback_data: dict, state: FSMContext):
    step: str = callback_data.get("step")
    if step == "":
        await state.finish()
        await call.message.edit_text(ORDER_MESSAGES["exit"])

def get_cancel_kb(step: str = ""):
    cancel_button = get_cancel_button(step)
    return InlineKeyboardMarkup().add(cancel_button)

cancel_button1 = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Назад", callback_data="nazad_button")
)

cancel_button2 = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Назад", callback_data="nazad_button2")
)

cancel_button3 = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Назад", callback_data="nazad_button3")
)

cancel_button4 = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text="Назад", callback_data="nazad_button4")
)

class Form(StatesGroup):
    pib = State()
    abonplata = State()
    phone = State()
    address = State()
    captcha = State()

    canceled = State()

class Mailing(StatesGroup):
    Text = State()
    canceled = State()

class SupportStates(StatesGroup):
    commercial_msg = State()
    waiting_live = State()
    busy = State()

stop_button = [InlineKeyboardButton(text="❌Скасувати", callback_data="stop_rozsulka")]
stop_keyboard  = InlineKeyboardMarkup(inline_keyboard=[stop_button])

# ВІДПРАВЛЕННЯ АБСОЛЮТНО ВСІХ ПОВІДОМЛЕНЬ В САППОРТ
@dp.message_handler(
    state=SupportStates.busy,
    content_types=ContentType.ANY,
)
async def send_msg_to_support_many(message: Message, state: FSMContext):
    data = await state.get_data()
    second_id = data["second_id"]
    try:
        await message.copy_to(second_id, reply_markup=cancel_support)
    except BotBlocked:
        await message.reply("Користувач заблокував бота")
    except Exception as error:
        await message.reply("Не відправлено")
        await send_error_chat(f"Помилка в підтримці: {error}")

@dp.message_handler(commands=['start'], state = '*')
async def start(message: types.Message, state:FSMContext):
	await state.finish()
	with sq.connect("clients.db") as con:
		cur = con.cursor()
		cur.execute(f"""SELECT id FROM users WHERE id LIKE {message.from_user.id}""")
		user = str(cur.fetchall())
		if user == str([]):
			cur.execute(f"INSERT INTO users VALUES({str(message.from_user.id)})")
		else:
			pass

		choice = InlineKeyboardMarkup(
            inline_keyboard=[

                [InlineKeyboardButton(text="Підтримка", callback_data="support")],
                [InlineKeyboardButton(text="Оплата послуг", callback_data="Оплата послуг")]])
		await message.answer(f"<b>Доброго часу доби,</b> {message.from_user.first_name}"
                             f"\nВітаємо у Telegram-bot - <b>Інтернет провайдера SkyNet</b>"
                             f"\n\nВибери кнопкою 'Підтримка' та зв'яжись з нашим оператором,або якщо ти не оплатив за Internet - можеш зробити це прямо зараз!\n\n👨🏻‍💻Розробник:N.Ivakhiv",
                             parse_mode='html', reply_markup=choice)

@dp.callback_query_handler(lambda call: call.data == 'Оплата послуг')
async def inet(call: CallbackData):
    await Form.pib.set()
    await call.answer()
    await bot.send_message(call.from_user.id, "Вкажіть ПІБ:\nЯкий є вказаний у договорі з нами.")

@dp.message_handler(state=Form.pib)
async def process_pib(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['pib'] = message.text
        await Form.next()
        await bot.send_message(message.from_user.id, "Вкажіть вартість вашого місячного тарифного плану який є зазначений у договорі", reply_markup=cancel_button1)

@dp.callback_query_handler(lambda call: call.data == "nazad_button", state=Form.abonplata)
async def process_pib_nazad(call: types.Message, state: FSMContext):
    await call.answer()
    await Form.pib.set()
    await bot.send_message(call.from_user.id, "Вкажіть ПІБ:\nЯкий є вказаний у договорі з нами.")

@dp.message_handler(state=Form.abonplata)
async def process_abonplata(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if((message.text).isdigit()):
            data['abonplata'] = message.text
            await Form.next()
            await bot.send_message(message.from_user.id, "Вкажіть номер телефону!\nВ форматі +380..", reply_markup=cancel_button2)
        else:
            await bot.send_message(message.from_user.id, "Це не число! Повторіть введення")

@dp.callback_query_handler(lambda call: call.data == "nazad_button2", state=Form.phone)
async def process_aboplata_nazad(call: types.Message, state: FSMContext):
    await call.answer()
    await Form.abonplata.set()
    await bot.send_message(call.from_user.id, "Вкажіть вартість вашого місячного тарифного плану який є зазначений у договорі")

@dp.message_handler(lambda message: not len(message.text)==13, state=Form.phone)
async def process_phone_invalid(message: types.Message):
    return await bot.send_message(message.from_user.id, "Введіть коректний номер телефону")

@dp.callback_query_handler(lambda call: call.data == "nazad_button3", state=Form.address)
async def process_phone_nazad(call: types.Message, state: FSMContext):
    await call.answer()
    await Form.phone.set()
    await bot.send_message(call.from_user.id, "Вкажіть номер телефону!\nВ форматі +380..")

@dp.message_handler(lambda message: '+380' in (message.text) and len(message.text)==13 and message.text[1:12].isdigit(), state=Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await Form.next()
    await state.update_data(phone=(message.text))
    await bot.send_message(message.from_user.id, "📍Ваша адреса?\nВкажіть населений пункт, вулицю та будинок.", reply_markup=cancel_button3)

@dp.message_handler(state=Form.address)
async def process_gender(message: types.Message, state: FSMContext):
    await Form.next()
    async with state.proxy() as data:
        data['address'] = message.text
    await state.update_data(address=(message.text))

    image = ImageCaptcha(fonts=['fonts/A.ttf', 'fonts/A.ttf'])
    global captcha_num
    captcha_num = str(random.randint(1000, 9999))
    image.write(captcha_num, 'captcha.png')

    await bot.send_photo(message.from_user.id, photo=open('captcha.png', "rb"))

    await bot.send_message(message.from_user.id, "Підтвердіть що ви не робот:", reply_markup=cancel_button4)

@dp.callback_query_handler(lambda call: call.data == "nazad_button4", state=Form.captcha)
async def process_captcha_nazad(call: types.Message, state: FSMContext):
    await call.answer()
    await Form.address.set()
    await bot.send_message(call.from_user.id, "📍Ваша адреса?")

@dp.message_handler(lambda message: str(message.text)!=captcha_num, state=Form.captcha)
async def process_captcha_invalid(message: types.Message):
    await bot.send_message(message.from_user.id, "Невірно! Спробуйте ще")

oplata_callback = CallbackData("оплата", "choice", "amount")
@dp.message_handler(lambda message: str(message.text)==captcha_num, state=Form.captcha)
async def process_captcha(message: types.Message, state: FSMContext):
    await state.update_data(captcha=(message.text))

    datatime_ua = datetime.now(pytz.timezone("Europe/Kiev"))
    datatime_ua = f"{str(datatime_ua)[0:10]}-{str(datatime_ua)[11:19]}"

    async with state.proxy() as data:
     name = (data['pib'])

    order = md.text(
                md.text("👤Ім'я:", (data['pib'])),
                md.text('☎Телефон:', (data['phone'])),
                md.text("💰Ціна послуг:", (data['abonplata']) + "грн"),
                md.text('🏠Адреса:', (data['address'])),
                md.text('⌚Час:', (datatime_ua)), sep='\n')
    perevirka = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅Так", callback_data=oplata_callback.new(choice='yes', amount=(data['abonplata'])))],
            [InlineKeyboardButton(text="❌Ні", callback_data="no")]])
    await state.update_data(order=str(order))
    await bot.send_message(message.chat.id, f'{md.text("Вірні ваші дані?", md.bold())}\n{order}', parse_mode="Markdown", reply_markup = perevirka)

@dp.callback_query_handler(lambda call: call.data == 'no', state=Form.captcha)
async def perevikra_no(call: CallbackData):
    await bot.send_message(call.message.chat.id, f"Ви скасували замовлення", parse_mode="Markdown")
    await bot.delete_message(call.message.chat.id, call.message.message_id)

@dp.callback_query_handler(oplata_callback.filter(choice='yes'), state=Form.captcha)
async def perevikra_yes(call: CallbackData, callback_data, state:FSMContext):
    await bot.send_document(call.message.chat.id, document=open('file/Договір.pdf', 'rb'), caption="Згідно статті 633 ЦК України ви даєте згоду на ПУБЛІЧНУ ОФЕРТУ\n\nМи раді що ви правильно заповнили дані, оплатіть будь ласка ваш тариф👇🏻", parse_mode="HTML") 
    await call.message.edit_reply_markup()
    await bot.send_invoice(call.message.chat.id, title = 'Оплата послуг SkyNet',
    description='Ви оплачуєте місячну абноплату за наші послуги згідно нашого договору з вами.',
    provider_token=config.LIQPAY_PROVIDER_TOKEN,
    prices=[
            types.LabeledPrice(label='Оплата за місячні послуги:', amount=int(callback_data['amount'])*100),
          ],
        currency='uah',
        payload="test",
        start_parameter='time-machine-example',
        )

# Підтвердження, чи все правильно в замовленні
@dp.pre_checkout_query_handler(state=Form.captcha)
async def checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Оплата пройшла успішно
@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT, state=Form.captcha)
async def got_payment(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id,
        'Сплачено {} {}'.format(
            message.successful_payment.total_amount / 100,
            message.successful_payment.currency
        ),
    parse_mode='Markdown')
    data = await state.get_data()
    await bot.send_message(config.error, f'Людина оплатила послугу: {data["order"]}')
    await state.finish()

# ========= ПІДТРИМКА =========


async def check_support_available(support_id):
    state = dp.current_state(chat=support_id, user=support_id)
    current_state = await state.get_state()
    if current_state == SupportStates.busy.state:
        return False
    return support_id


async def get_free_supports():
    ids = config.support_ids
    random.shuffle(ids)
    free_ids = []
    for support_id in ids:
        support_id = await check_support_available(support_id)

        if support_id:
            free_ids.append(support_id)

    return free_ids


async def send_msg_commercial(message: Message, to_ids=None):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            "Відповісти",
            callback_data=send_commercial_cb.new(user_id=message.from_user.id),
        )
    )
    for user_id in to_ids:
        await bot.send_message(
            user_id, "Вам лист! Ви можете на нього відповісти на кнопку нижче."
        )
        await message.copy_to(user_id, reply_markup=keyboard)


@dp.callback_query_handler(Text(equals="support"))
async def support(call: CallbackQuery):
    await call.answer(cache_time=5)
    keyboard = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Новояворівськ", callback_data="support_live1"),
        InlineKeyboardButton(text="Шкло", callback_data="support_live2"),
        InlineKeyboardButton(text="Старичі", callback_data="support_live3"),
        InlineKeyboardButton(text="Підлуби", callback_data="support_live4"),
        InlineKeyboardButton(text="Бердихів", callback_data="support_live5"),
        InlineKeyboardButton(text="Молошковичі", callback_data="support_live6"),
        InlineKeyboardButton(text="Верещиця", callback_data="support_live7"),
        )
    await call.message.answer(
        "Виберіть будь ласка свій населенний пункт для з'єднання повноваженого оператора.",
        reply_markup=keyboard,
    )


@dp.callback_query_handler(Text(equals="support_commercial"))
async def send_commercial(call: CallbackQuery):
    await SupportStates.commercial_msg.set()
    await call.message.answer("Надішліть повідомлення", reply_markup=get_cancel_kb())
    await call.answer()


@dp.callback_query_handler(send_commercial_cb.filter())
async def answer_commercial(
    call: CallbackQuery, callback_data: dict, state: FSMContext
):
    await SupportStates.commercial_msg.set()
    await state.update_data(second_id=callback_data["user_id"])
    await call.message.answer("Надішліть відповідь", reply_markup=get_cancel_kb())
    await call.answer()


@dp.message_handler(state=SupportStates.commercial_msg, content_types=ContentType.ANY)
async def process_commercial(message: Message, state: FSMContext):
    data = await state.get_data()
    second_id = data.get("second_id")
    await state.finish()

    status_msg = await message.answer("Відправлення...")
    # Якщо не вказано second_id, значить це не відповідь і відсилати всім
    if second_id is None:
        await send_msg_commercial(message, to_ids=config.commercial_ids)
    else:
        await send_msg_commercial(message, to_ids=[second_id])
    await status_msg.edit_text("Ви відправили це повідомлення!")


@dp.callback_query_handler(Text(equals="support_live1"))
async def call_support(call: CallbackQuery):
    await call.answer()
    now = datetime.now(TIMEZONE)
    start_date = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=55, microsecond=0)

    if now < start_date or now > end_date:
        await call.message.answer("Служба підтримки Telegram працює з тільки 8:00 до 00:00")
        return

    support_ids = config.support_ids_nya
    if not support_ids:
        await call.message.edit_text(
            "На жаль, не має вільних операторів. Спробуйте пізніше."
        )
        return

    await SupportStates.waiting_live.set()
    await call.message.edit_text(
        "Ви звернулись в техпідтримку. Очікуємо відповіді оператора!",
        reply_markup=get_cancel_kb(),
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Відповісти",
            callback_data=answer_live_cb.new(user_id=call.from_user.id),
        )
    )

    for user_id in support_ids:
        await bot.send_message(
            user_id,
            f"З вами хоче звязатись користувач {call.from_user.get_mention()}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

#############################################################

@dp.callback_query_handler(Text(equals="support_live2"))
async def call_support(call: CallbackQuery):
    await call.answer()
    now = datetime.now(TIMEZONE)
    start_date = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=55, microsecond=0)

    if now < start_date or now > end_date:
        await call.message.answer("Служба підтримки Telegram працює з тільки 8:00 до 00:00")
        return

    support_ids = config.support_ids_shklo
    if not support_ids:
        await call.message.edit_text(
            "На жаль, не має вільних операторів. Спробуйте пізніше."
        )
        return

    await SupportStates.waiting_live.set()
    await call.message.edit_text(
        "Ви звернулись в техпідтримку. Очікуємо відповіді оператора!",
        reply_markup=get_cancel_kb(),
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Відповісти",
            callback_data=answer_live_cb.new(user_id=call.from_user.id),
        )
    )

    for user_id in support_ids:
        await bot.send_message(
            user_id,
            f"З вами хоче звязатись користувач {call.from_user.get_mention()}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

###########################################################

@dp.callback_query_handler(Text(equals="support_live3"))
async def call_support(call: CallbackQuery):
    await call.answer()
    now = datetime.now(TIMEZONE)
    start_date = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=55, microsecond=0)

    if now < start_date or now > end_date:
        await call.message.answer("Служба підтримки Telegram працює з тільки 8:00 до 00:00")
        return

    support_ids = config.support_ids_shklo
    if not support_ids:
        await call.message.edit_text(
            "На жаль, не має вільних операторів. Спробуйте пізніше."
        )
        return

    await SupportStates.waiting_live.set()
    await call.message.edit_text(
        "Ви звернулись в техпідтримку. Очікуємо відповіді оператора!",
        reply_markup=get_cancel_kb(),
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Відповісти",
            callback_data=answer_live_cb.new(user_id=call.from_user.id),
        )
    )

    for user_id in support_ids:
        await bot.send_message(
            user_id,
            f"З вами хоче звязатись користувач {call.from_user.get_mention()}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

###########################################################################################

@dp.callback_query_handler(Text(equals="support_live7"))
async def call_support(call: CallbackQuery):
    await call.answer()
    now = datetime.now(TIMEZONE)
    start_date = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=55, microsecond=0)

    if now < start_date or now > end_date:
        await call.message.answer("Служба підтримки Telegram працює з тільки 8:00 до 00:00")
        return

    support_ids = config.support_ids_shklo
    if not support_ids:
        await call.message.edit_text(
            "На жаль, не має вільних операторів. Спробуйте пізніше."
        )
        return

    await SupportStates.waiting_live.set()
    await call.message.edit_text(
        "Ви звернулись в техпідтримку. Очікуємо відповіді оператора!",
        reply_markup=get_cancel_kb(),
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Відповісти",
            callback_data=answer_live_cb.new(user_id=call.from_user.id),
        )
    )

    for user_id in support_ids:
        await bot.send_message(
            user_id,
            f"З вами хоче звязатись користувач {call.from_user.get_mention()}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

#################################################################

@dp.callback_query_handler(Text(equals="support_live4"))
async def call_support(call: CallbackQuery):
    await call.answer()
    now = datetime.now(TIMEZONE)
    start_date = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=55, microsecond=0)

    if now < start_date or now > end_date:
        await call.message.answer("Служба підтримки Telegram працює з тільки 8:00 до 00:00")
        return

    support_ids = config.support_ids_berdikhiv
    if not support_ids:
        await call.message.edit_text(
            "На жаль, не має вільних операторів. Спробуйте пізніше."
        )
        return

    await SupportStates.waiting_live.set()
    await call.message.edit_text(
        "Ви звернулись в техпідтримку. Очікуємо відповіді оператора!",
        reply_markup=get_cancel_kb(),
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Відповісти",
            callback_data=answer_live_cb.new(user_id=call.from_user.id),
        )
    )

    for user_id in support_ids:
        await bot.send_message(
            user_id,
            f"З вами хоче звязатись користувач {call.from_user.get_mention()}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

##########################################################################

@dp.callback_query_handler(Text(equals="support_live5"))
async def call_support(call: CallbackQuery):
    await call.answer()
    now = datetime.now(TIMEZONE)
    start_date = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=55, microsecond=0)

    if now < start_date or now > end_date:
        await call.message.answer("Служба підтримки Telegram працює з тільки 8:00 до 00:00")
        return

    support_ids = config.support_ids_berdikhiv
    if not support_ids:
        await call.message.edit_text(
            "На жаль, не має вільних операторів. Спробуйте пізніше."
        )
        return

    await SupportStates.waiting_live.set()
    await call.message.edit_text(
        "Ви звернулись в техпідтримку. Очікуємо відповіді оператора!",
        reply_markup=get_cancel_kb(),
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Відповісти",
            callback_data=answer_live_cb.new(user_id=call.from_user.id),
        )
    )

    for user_id in support_ids:
        await bot.send_message(
            user_id,
            f"З вами хоче звязатись користувач {call.from_user.get_mention()}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

##############################################################################

@dp.callback_query_handler(Text(equals="support_live6"))
async def call_support(call: CallbackQuery):
    await call.answer()
    now = datetime.now(TIMEZONE)
    start_date = now.replace(hour=8, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=55, microsecond=0)

    if now < start_date or now > end_date:
        await call.message.answer("Служба підтримки Telegram працює з тільки 8:00 до 00:00")
        return

    support_ids = config.support_ids_berdikhiv
    if not support_ids:
        await call.message.edit_text(
            "На жаль, не має вільних операторів. Спробуйте пізніше."
        )
        return

    await SupportStates.waiting_live.set()
    await call.message.edit_text(
        "Ви звернулись в техпідтримку. Очікуємо відповіді оператора!",
        reply_markup=get_cancel_kb(),
    )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Відповісти",
            callback_data=answer_live_cb.new(user_id=call.from_user.id),
        )
    )

    for user_id in support_ids:
        await bot.send_message(
            user_id,
            f"З вами хоче звязатись користувач {call.from_user.get_mention()}",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )

###############################################

@dp.message_handler(state=SupportStates.waiting_live, content_types=ContentType.ANY)
async def not_now_supported(message: Message):
    await message.answer(
        "Дочекайтесь відповіді оператора або відмініть сеанс",
        reply_markup=get_cancel_kb(),
    )

@dp.callback_query_handler(answer_live_cb.filter())
async def answer_support_call(
    call: CallbackQuery, state: FSMContext, callback_data: dict
):
    support_id = call.from_user.id
    user_id = int(callback_data.get("user_id"))
    user_state = dp.current_state(user=user_id, chat=user_id)

    if await user_state.get_state() != SupportStates.waiting_live.state:
        await call.message.edit_text("З клієнтом вже спілкуються або він передумав")
        return

    await state.set_state(SupportStates.busy.state)
    await state.update_data(second_id=user_id, is_support=True)

    await user_state.set_state(SupportStates.busy.state)
    await user_state.update_data(second_id=support_id, is_support=False)

    await call.message.edit_text(
        "Ви на звязку із користувачем!\n"
        "Щоб завершити розмову натисніть кнопку нижче.",
        reply_markup=cancel_support,
    )
    await bot.send_message(
        user_id,
        "Техпідтримка на звязку! Можете писати сюди свої повідомлення.\n"
        "Щоб завершити спілкування натисніть на кнопку нижче.",
        reply_markup=cancel_support,
    )


@dp.callback_query_handler(Text(equals="cancel_support"), state=SupportStates.busy)
async def exit_support(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_support = data["is_support"]
    second_id = data["second_id"]
    second_state = dp.current_state(user=second_id, chat=second_id)
    await state.finish()
    await second_state.finish()

    if is_support:
        text = "Техпідтримка закінчила сеанс підтримки"
    else:
        text = "Користувач завершив сеанс техпідтримки"

    try:
        await bot.send_message(second_id, text)
    except Exception:
        pass

    await call.message.edit_text("Ви завершили сеанс")

############################################
#####=========ДОВІДНИК======################
############################################

@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id:
        button_1 = KeyboardButton('Як підключити роутер')
        button_2 = KeyboardButton('Чому треба час від часу перезагружати роутер')
        button_3 = KeyboardButton('Як завантажити наш додаток')
        button_4 = KeyboardButton('Відсутнє з‘єднання є інтернетом?')
        button_5 = KeyboardButton('Як підключити ТБ')
        button_6 = KeyboardButton('Посилання на наш веб-сайт')
        button_7 = KeyboardButton('Посилання на сайт оплати EasyPay')
        button_8 = KeyboardButton('Посилання на особистий кабінет користувача')
        button_9 = KeyboardButton('Посилання на наш Instagram')
        button_10 = KeyboardButton('Наші контакти')
        button_11 = KeyboardButton('Наші тарифи')
        button_12 = KeyboardButton('Контакти розробника')
        button_13 = KeyboardButton('Вийти з довідника')

        greet_kb = ReplyKeyboardMarkup(
    resize_keyboard=True
).add(button_1).add(button_2).add(button_3).add(button_4).add(button_5).add(button_6).add(button_7).add(button_8).add(button_9).add(button_10).add(button_11).add(button_12).add(button_13)
        
        await message.reply("Вітаємо вас у довіднику Новояворівської мережі SkyNet", reply_markup=greet_kb)

@dp.message_handler(lambda message: message.text == 'Наші контакти')
async def restartmodem(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Інтернет провайдер СкайНет\nм.Новояворівськ\nвул. С.Бандери, 17 (біля УкрПошти)\nsupport@skynet-lan.org\n\nТелефони техпідтримки:\nНовояворівськ (093) 97-64-405 | (068) 50-20-452\n\nШкло, Старичі, Верещиця (068) 68-31-891", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Чому треба час від часу перезагружати роутер')
async def restartmodem(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Незалежно від потужності та вартості вашого роутера, від безперервної роботи і великої кількості підключених до нього пристроїв, роутер може зависати. При цьому усі індикатори показують,що він працює справно, проте для відновлення підключення інтернету ми радимо відключати пристрій за допомогою кнопки живлення, або ж просто від‘єднати його від розетки на 10 хв.За цей час ваш роутер отримає нову ip-адресу і відновить стабільне підключення з інтернетом.", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Як завантажити наш додаток')
async def prilogenia(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Завантажити додаток можна за посиланнями 👉 "'<a href="https://play.google.com/store/apps/details?id=com.softering.skynet">Play Market (Android)</a>'" або " '<a href="https://apps.apple.com/us/app/skynet/id1484172373?l=ru&ls=1">AppStore(IOS)</a>'"", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Як підключити роутер')
async def router(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Покрокова інструкція, як підключити свій роутер самостійно.\n\n•Перш за все, для підключення під‘єднайте інтернет-кабель у WAN-порт вашого роутера (зазвичай, він виділений окремим кольором на задній частині корпусу).\n\n•Після цього знайдіть на нижній частині роутера заводську наклейку із вказаними на ній назвою Wifi-мережі і паролем до неї.\nВаш роутер підключено.\n\nДалі знайдіть на пристрої, який підключатимете до Wifi (телефон, ноутбук) назву вашої мережі та введіть свій пароль.\nГотово! ", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Наші тарифи')
async def taruf(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Ознайомитись з нашими тарифами 👉 "'<a href="https://www.skynet-lan.org/taryfy.html">Тарифи</a>'"", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Посилання на наш веб-сайт')
async def sayt(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Наш веб-сайт 👉 "'<a href="http://skynet-lan.org/">SkyNet</a>'"", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Контакти розробника')
async def rozrab(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"👨‍💻Developed: Nazar Ivakhiv | @ivakhiv_off - Telegram", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Як підключити ТБ')
async def TB(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Телебачення без обмежень!\n\nПідключайте онлайн тв на тому сервісі, який оберете ви самі без будь яких обмежень.\n\nДля зручності ми зібрали найбільш поширені сервіси з українським та іноземним телебаченням, підключити які можна за допомогою цих сайтів:\n\n"'<a href="https://oll.tv/ru/oixs_offer">•OLL.TV</a>'"\n"'<a href="https://megogo.net/ua">•MEGOGO.NET</a>'"\n"'<a href="https://omegatv.ua/">•OmegaTV.ua</a>'"\n"'<a href="https://divan.tv/">•DIVAN.TV</a>'"\n"'<a href="https://sweet.tv/">•SWEET.TV</a>'"\n\nДля початку роботи з сервісами необхідно зареєструватись на сайті обраного вами постачальника телебачення та обрати той тарифний план, який вам найбільше підходить.\n\nДля подальної роботи, а також оплати послуг  користуйтесь інструкціями і підказками на сайтах постачальників та насолоджуйтесь переглядом улюблених телевізійних програм і фільмів.", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Посилання на наш Instagram')
async def inst(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Наш Instagram 👉 "'<a href="https://www.instagram.com/skynet_novoyavorivsk/">SkyNet</a>'"", parse_mode='html')        

@dp.message_handler(lambda message: message.text == 'Посилання на сайт оплати EasyPay')
async def easypay(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Оплата EasyPay 👉 "'<a href="https://easypay.ua/catalog/internet/skynet">EasyPay SkyNet</a>'"", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Посилання на особистий кабінет користувача')
async def saytkab(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Авторизуватись на особистому кабінеті користувача 👉 "'<a href="http://next.e-xata.net.ua/cgi-bin/stat.pl">Кабінет SkyNet</a>'"", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Відсутнє з‘єднання є інтернетом?')
async def propavinet(message):
    user_id = str(message.from_user.id)
    if user_id:

        await bot.send_message(message.chat.id, f"Причин може бути безліч, проте є 4 найчастіші, які кожен наш абонент може перевірити самостійно.\nЗберігай, щоб не загубити публікацію😉\n\n💠Недостатньо коштів на рахунку. Звучить банально, проте це найчастіша причина. Щоб подібного не ставалось, завантажуй додаток SkyNet та отримуй інформацію про стан особистого рахунку за лічені секунди, а також миттєво поповнюй.\n\n💠Завис роутер. Іноді навіть найкраща техніка може дати збій. У такій ситуації просто вимкни твій роутер на 10 хвилин, після цього увімкни та перевір інтернет з‘єднання.\n\n💠Перебитий кабель. Дуже часто причиною цьому є домашні тварини, які полюбляють гризти мережевий кабель, або важкі меблі, які можуть випадково поставити зверху. Перевір можливі проблеми з кабелем просто візуально оглянувши його, і при виявленні проблеми телефонуй на нашу службу підтримки: (068) 50 20 452.\n\n💠Інтернет-кабель вставлений в помилковий порт. Зверни увагу, переважна більшість виробників виділяють порт для мережевого кабеля іншим кольором, або познають словом “internet”, “wan”.\n\nЯкщо ж причина в іншому, телефонуй у нашу службу підтримки, тобі нададуть інформацію по можливих неполадках, або завітають до тебе, щоб їх усунути.", parse_mode='html')  

@dp.message_handler(lambda message: message.text == 'Вийти з довідника')
async def stop(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id:
        del_buttons = ReplyKeyboardRemove()
        await message.reply("Ви вийшли з довідника,та можете повернутись в головне меню 👉 /start",reply_markup=del_buttons)

##############################################
######=========ADMIN========##################
##############################################

@dp.message_handler(commands=['adm','admin'])
async def adm(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in config.admin:
        button_1 = KeyboardButton('Зберегти базу')
        button_2 = KeyboardButton('Користувачі')
        button_3 = KeyboardButton('Розсилка')
        button_4 = KeyboardButton('Закрити')

        greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
        greet_kb.add(button_1, button_2, button_3, button_4)

        await message.reply("Адмін-панель успішно відкрита", reply_markup=greet_kb)

@dp.callback_query_handler(lambda call: call.data == 'stop_rozsulka' , state='*')
async def perevikra_no(call: CallbackData,state: FSMContext):
    await bot.send_message(call.message.chat.id, f"Ви скасували розсилку.", parse_mode="Markdown")
    await call.message.edit_reply_markup()
    await state.finish()

@dp.message_handler(lambda message: message.text == 'Закрити')
async def stop(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in config.admin:
        del_buttons = ReplyKeyboardRemove()
        await message.reply("Ви вийшли з адмін-панелі",reply_markup=del_buttons)

@dp.message_handler(lambda message: message.text == 'Зберегти базу')
async def save(message):
    user_id = str(message.from_user.id)
    if user_id in config.admin:
        save = open("clients.db", 'rb')
        await bot.send_document(message.from_user.id, save, reply_to_message_id=message.message_id)

@dp.message_handler(lambda message: message.text == 'Користувачі')
async def users(message):
    user_id = str(message.from_user.id)
    if user_id in config.admin:
        with sq.connect("clients.db") as con:
            cur = con.cursor()

        cur.execute(f"SELECT count(*) FROM users")

        stat = str(cur.fetchall()[0][0])
        await bot.send_message(message.chat.id, f"У боті зареєстровано: <b>{stat}</b> користувача!", parse_mode='html')

@dp.message_handler(lambda message: message.text == 'Розсилка')
async def rozsulka(message):
    user_id = str(message.from_user.id)
    if user_id in config.admin:
        await message.reply('Очікую повідомлення...' , reply_markup=stop_keyboard)
        await Mailing.Text.set()

@dp.message_handler(state=Mailing.Text, content_types=types.ContentType.ANY)
async def rozsulka_full(message: types.Message, state: FSMContext):
    with sq.connect("clients.db") as con:
        cur = con.cursor()

    cur.execute(f"""SELECT id FROM users""")
    call_sp = cur.fetchall()

    error = 0
    good = 0
    while call_sp != []:
        first_user = call_sp[0][0]
        del [call_sp[0]]
        try:
            await message.copy_to(first_user)
            good += 1
        except:
            error += 1
    await bot.send_message(config.error, f"Розсилка: \nУспішно: {good} \nНе прийшло: {error}")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)