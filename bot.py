import logging
import aiogram.utils.exceptions
from aiogram import Bot, Dispatcher, executor, types
from sql_operator import TasksDB, MyTask, MyUser
import json
import sys


def exception_hook(exc_type, exc_value, tb):
    # custom exception hook for some weird errors.
    logging.critical(f"{exc_type.__name__}: {exc_value} ({tb.tb_lineno})")


def load_cats():
    # load task categories from file
    with open("cats.json", 'r') as j:
        return json.loads(j.read())


with open('my.token') as token:
    API_TOKEN = token.read()

# load long answers
with open('replies/help.txt') as f:
    reply_help = f.read()

with open('replies/manual.txt') as f:
    reply_manual = f.read()

# configure logging
sys.excepthook = exception_hook
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO,
                    filename="bot_log.txt")

# initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
bot.set_chat_menu_button()
dp = Dispatcher(bot)
db = TasksDB("db.sqlite3")
cats = load_cats()
# create keyboards

# menu keyboard
menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_kb.add(types.KeyboardButton("📖 Ботать"))
menu_kb.add(types.KeyboardButton("📊 Статистика"))
menu_kb.add(types.KeyboardButton("❓ Помощь"))

# back keyboard (only back button)
back_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_kb.add(types.KeyboardButton("➡️ Назад"))

# task keyboard (with skip option)
ans_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
ans_kb.add(types.KeyboardButton("➡️ Другое задание"))
ans_kb.add(types.KeyboardButton("⏹ Выйти в меню"))

# task keyboard (with next option)
ans_kb2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
ans_kb2.add(types.KeyboardButton("➡️ Дальше"))
ans_kb2.add(types.KeyboardButton("⏹ Выйти в меню"))

# all task keyboard
task_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
for i in range(5):
    def p(x):
        return list(cats.keys())[x - 1]
    j = i * 5
    task_kb.row(types.KeyboardButton(p(j + 1)), types.KeyboardButton(p(j + 2)), types.KeyboardButton(p(j + 3)),
                types.KeyboardButton(p(j + 4)), types.KeyboardButton(p(j + 5)))


logging.info("Pre-init success.")


def format_task(task: MyTask):
    """
    Prepare task to be sent: replace < and > symbols, attach files and code if needed
    """
    out = task.text.replace('&', '&amp').replace('<', '&lt').replace('>', '&gt')
    if task.file_url:
        links = task.file_url.split(" ")
        out += '\n'
        if len(links) == 1:
            # single file
            out += f"\n<a href='{task.file_url}'>📄 Файлик</a>"
        else:
            # several files
            for link_i, link in enumerate(links):
                out += f"<a href='{link}'>\n📄 Файлик {link_i + 1}</a>"
    if task.code:
        out += f"\n<code>{task.code.replace('&', '&amp').replace('<', '&lt').replace('>', '&gt')}</code>"
    return out


def format_stats(user):
    """
    Generate statistics.
    """
    out = "<b>Ваша статистика:</b>\n<pre>"
    out += f'№      В    Н    %\n'
    for ege_id in list(cats.keys())[:-1]:
        solved_w = db.get_all_solved(user, ege_id=ege_id, solved=0)  # solved wrong
        solved_r = db.get_all_solved(user, ege_id=ege_id, solved=1)  # solved right
        if solved_r is None and solved_w is None:
            # no data
            out += f'{str(ege_id).ljust(6, " ")} -    -    -\n'
        else:
            # generate pre-formatted strings
            solved_r = str(len(solved_r) if solved_r is not None else 0).ljust(4, " ")
            solved_w = str(len(solved_w) if solved_w is not None else 0).ljust(4, " ")
            percent = str(round((int(solved_r) * 100) // (int(solved_r) + int(solved_w))))
            # append string to output text
            out += f'{str(ege_id).ljust(6, " ")} {solved_r} {solved_w} {percent}%\n'
    out += '</pre>'
    return out


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
    Default greet text. (/start)
    Also adds user in the db.
    """
    await message.answer("👋 Привет!\nЯ помогу тебе ботать информатику.\nДля быстрого ознакомления используй:\n"
                         "/help - справка по работе с ботом\n"
                         "/manual - инструкция по работе с заданиями", reply_markup=menu_kb)
    db.update_user(MyUser(message.from_user.id, message.chat.id))
    logging.info(f"New user: {message.from_user.id} {message.from_user.username}")


@dp.message_handler(commands=['menu'])
async def menu(message: types.Message):
    """
    Return to menu.
    """
    await message.answer(
        "<b>Меню</b>\nЧтобы начать ботать, пропиши /solve\nЧтобы перейти к конкретному заданию, пропиши /task\nЧ"
        "тобы посмотреть статистику, пропиши /stats\nВернутся сюда ты можешь всегда, прописав /menu",
        reply_markup=menu_kb, parse_mode=types.ParseMode.HTML)
    db.update_user(MyUser(message.from_user.id, message.chat.id))


@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    """
    Send statistics.
    """
    await message.answer(format_stats(message.from_user.id), parse_mode=types.ParseMode.HTML)


@dp.message_handler(commands=['manual'])
async def manual(message: types.Message):
    """
    Send user manual.
    """
    await message.answer(reply_manual, parse_mode=types.ParseMode.HTML)


@dp.message_handler(commands=['solve'])
async def start_solve(message: types.Message):
    """
    Start solving random tasks.
    """
    message.text = message.text.replace("/solve", "")  # leave command arguments
    db.update_user(MyUser(message.from_user.id, message.chat.id, ege_id=0))  # wait for task select
    if message.text:
        # if some arguments provided, emulate user answer
        message.text = message.text[1:]  # remove space between
        await echo(message)
    else:
        # otherwise wait for user answer
        await message.answer("👌 Поехали! Введи номер задания [1; 27]:", reply_markup=task_kb)


@dp.message_handler(commands=['task'])
async def get_task(message: types.Message):
    """
    Get specific task.
    """
    text = message.text.replace("/task", "")
    if text:
        # if a command argument is provided
        try:
            # try to get task from db
            task = db.get_task(int(text))
            if task:
                # if ok, send task to user and wait for its answer
                await send_task(message, task, back_kb)
                db.update_user(MyUser(message.from_user.id, message.chat.id, task.id))
            else:
                # no task
                await message.answer("😕 Задание не найдено.")
        except ValueError:
            # wrong argument
            await message.answer("😟 Это точно номер?")
    else:
        # wait for task select
        db.update_user(MyUser(message.from_user.id, message.chat.id, 0))
        await message.answer("👌 Введи номер задания:")


async def send_task(message: types.Message, task: MyTask, reply_markup):
    """
    Send prepared task with photos.
    """
    if task:
        if task.image_url:
            # task has an image
            try:
                # try to send task
                await bot.send_photo(message.chat.id, task.image_url, format_task(task),
                                     parse_mode=types.ParseMode.HTML, reply_markup=reply_markup)
            except aiogram.utils.exceptions.BadRequest:
                # media caption too long error. Send photo and task separately
                await message.answer(format_task(task), parse_mode=types.ParseMode.HTML, reply_markup=reply_markup)
                await bot.send_photo(message.chat.id, task.image_url, "🖼 Картинка",
                                     parse_mode=types.ParseMode.HTML, reply_markup=reply_markup)
        else:
            # no image - just send
            await message.answer(format_task(task), parse_mode=types.ParseMode.HTML, reply_markup=reply_markup)


async def next_task(message: types.Message):
    """
    Skip current task and select another.
    """
    user = db.get_user(message.from_user.id)
    if str(user.ege_id) != '-1':
        # if user is actually solving some task
        new_task = db.select_unsolved(user.user_id, user.ege_id, user.cat_id)  # get new

        if new_task:
            # task found - send it
            await send_task(message, new_task, ans_kb)
            user.task = new_task.id
            db.update_user(user)
        else:
            # otherwise say that there are no tasks left
            await message.answer("✅ Вы решили все задания в этом категории!")
            await menu(message)
    else:
        # if user is not solving any task
        await message.answer("🤨 Ты сейчас ничего не решаешь. Куда дальше-то?")


@dp.message_handler(commands=['skip'])
async def skip(message: types.Message):
    await next_task(message)


@dp.message_handler(commands=['help'])
async def get_help(message: types.Message):
    await message.answer(reply_help, parse_mode=types.ParseMode.HTML)


@dp.message_handler()
async def echo(message: types.Message):
    """
    Non-command messages handler.
    """

    # some button bindings
    if message.text == "📖 Ботать":
        message.text = ''
        await start_solve(message)
    elif message.text == "❓ Помощь":
        await get_help(message)
    elif message.text == "⏹ Выйти в меню" or message.text == "➡️ Назад":
        await menu(message)
    elif message.text == '➡️ Дальше' or message.text == "➡️ Другое задание":
        await next_task(message)
    elif message.text == '📊 Статистика':
        await stats(message)
    else:
        # not a binding
        user = db.get_user(message.from_user.id)

        if user.task > 0:  # if some task is solved, check its answer
            # getting answer
            true_ans = db.get_task(user.task).answer

            # check if task was opened from /task (it is used for doing further actions)
            if user.ege_id == '-1' and str(user.cat_id) == '-1':
                is_single = True
            else:
                is_single = False

            # check if task was solved previously
            is_solved = db.is_solved(user.user_id, user.task)

            # handle all cases (right/wrong, first/second time)
            if str(message.text) == str(true_ans):
                if is_solved is None:
                    db.solve(user.user_id, user.task, 1)
                    ans = "😃 Верно!"
                elif is_solved:
                    ans = "😃 Верно! До этого ты тоже решил это задание правильно."
                else:
                    ans = "😃 Верно! До этого ты ошибся в этом задании."
                await message.answer(ans, reply_markup=(back_kb if is_single else ans_kb2))
            else:
                if is_solved is None:
                    db.solve(user.user_id, user.task, 0)
                    ans = f"😞 Неверно. Вот правильный ответ:\n<pre>{true_ans}</pre>"
                elif is_solved:
                    ans = f"😞 Неверно. Вот правильный ответ:\n<pre>{true_ans}</pre>\nРанее ты решил это задание " \
                          f"правильно."
                else:
                    ans = f"😞 Неверно, ты ошибаешся тут уже не первый раз! Вот правильный ответ:\n<pre>{true_ans}</pre>"
                await message.answer(ans, parse_mode=types.ParseMode.HTML,
                                     reply_markup=(back_kb if is_single else ans_kb2))
            user.task = -1
            db.update_user(user)

        elif int(user.task) == 0:
            # user is selecting task (/task)
            chosen_task = db.get_task(message.text)
            if chosen_task:
                await send_task(message, chosen_task, back_kb)
                user.task = chosen_task.id
                db.update_user(user)
            else:
                await message.answer("😕 Задание не найдено.")
                await menu(message)

        elif user.ege_id == '0':
            # user is selecting ege task

            # check some specific cases
            if message.text in ['19', '20', '21']:
                message.text = "19-21"

            if message.text in cats.keys():
                # task correct
                if len(cats[message.text]) > 1:
                    # task has several categories
                    buttons = []
                    for cat in list(cats[message.text].keys()) + ["Все"]:
                        buttons.append(types.KeyboardButton(cat))  # create keyboard

                    await message.answer(f"👇 Теперь выбери раздел\n" +
                                         '\n'.join([f"{x}: {cats[message.text][x]}" for x in cats[message.text]]),
                                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).row(*buttons))
                    db.update_user(MyUser(user.user_id, user.chat_id, -1, message.text, 0))
                else:
                    # task has single category - so we don't have to ask user
                    db.update_user(MyUser(user.user_id, user.chat_id, 0, message.text,
                                          list(cats[message.text].keys())[0]))
                    await next_task(message)
            else:
                # wrong ege task number
                await message.answer("😕 Ты ошибся номером, друг")
                await menu(message)

        elif user.cat_id == '0':
            # user is selecting category
            if message.text == 'Все' or message.text in list(cats[user.ege_id].keys()):
                # category chosen
                if message.text == 'Все':
                    t_cat = -1
                else:
                    t_cat = message.text
                db.update_user(MyUser(message.from_user.id, message.chat.id, 0, user.ege_id, t_cat))
                # successfully selected category
                await next_task(message)
            else:
                # wrong category
                await message.answer("😕 Неверная категория.")
                await menu(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    db.close()
