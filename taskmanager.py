import sqlite3
# pip install telebot
import telebot
from telebot import types 

# Database Configuration
DATABASE = "tasks.db"

# Telegram Configuration
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
bot = telebot.TeleBot(TOKEN) 


# Database Initialization and Core Functions
def setup_database(): 
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )''')
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description TEXT,
            completed BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        conn.commit()


def add_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()


def add_task(user_id, description):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (user_id, description, completed) VALUES (?, ?, 0)", (user_id, description))
        conn.commit()


def delete_task(task_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
        conn.commit()


def mark_completed(task_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET completed=1 WHERE task_id=?", (task_id,))
        conn.commit()


def get_tasks(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT task_id, description, completed FROM tasks WHERE user_id=?", (user_id,))
        return cur.fetchall()

# Telegram Bot Handlers


@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id)
    bot.reply_to(message, "Welcome to the Task Manager Bot!\nUse /add <task> to add a task, /list to list tasks, /delete <task_id> to delete.")


@bot.message_handler(commands=['add'])
def add_task_command(message):
    # Splitting the message into parts to determine if the user provided a task description
    parts = message.text.split(' ', 1)

    # If there's only one part, it means the user didn't provide a task description
    if len(parts) == 1:
        bot.reply_to(message, "Please provide a task description. Use: /add <your_task>")
        return

    # Extracting the task description
    task = parts[1]
    add_task(message.chat.id, task)
    bot.reply_to(message, f"Task '{task}' added!")


@bot.message_handler(commands=['list'])
def list_tasks_command(message):
    tasks = get_tasks(message.chat.id)
    if not tasks:
        bot.send_message(message.chat.id, "You have no tasks.")
        return
    
    for task in tasks: 
        task_id, description, completed = task
        status = "✅" if completed else "❌"
        
        markup = types.InlineKeyboardMarkup()
        button_text = "Mark as Done" if not completed else "Already Done"
        callback_data = f"done_{task_id}" if not completed else "noop" 
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
        
        bot.send_message(message.chat.id, f"{task_id}. {status} {description}", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def callback_mark_done(call):
    task_id = int(call.data.split("_")[1])
    mark_completed(task_id)
    bot.answer_callback_query(call.id, "Task marked as done!")
    bot.edit_message_text("✅ Task completed!", call.message.chat.id, call.message.message_id)


@bot.message_handler(commands=['delete'])
def delete_task_command(message):
    task_id = int(message.text.split(' ', 1)[1])
    delete_task(task_id)
    bot.reply_to(message, f"Task {task_id} deleted!")


# Initialize the database and start the bot
setup_database()


bot.polling(none_stop=True)
