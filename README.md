# KPolyakov telegram bot
This project contains a python https://kpolyakov.spb.ru/ tasks parser, a simple sql database operator and a telegram bot that can operate parsed tasks. This project is very specific and is rather for personal use.
<br><h2> Project structure </h2>
<h4> Scripts </h4>
<b>cat_parser.py</b> - This is simple script to parse task caterogies from website.
<b><br>tasks_parser.py</b> - Main tasks parser. Before running make sure that cats.json is generated, otherwise script won't work. Should be executed only if tasks update is required.
<b><br>replace_pows.js</b> - A script that replaces sub and sup html tags with unicode symbols as telegram doesn't yet support sup and sub tags.
<b><br>sql_operator.py</b> - Used both with bot and parser. Contains MyTask and MyUser classes (actual db models) and has some methods to simplfy working with db.
<b><br>bot.py</b> - Telegram bot. (aiogram)
<h4> Prepared data </h4>
<b>cats.json</b> - All task categories.
<b><br>db.sqlite3</b> - Prepared database.
<b><br>replies/</b> - Text files with large bot replies (/help, /manual).
