#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective paces.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import os
import logging
from dotenv import load_dotenv

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

import libvaasu


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

GET_ERP_USERNAME, GET_ERP_PASSWORD = range(2)

load_dotenv()

# For storing temporary values in conversations

temp = {
    'erpusernames': {}
}


def start(update, context):
    update.message.reply_text(
        'Hi there 👋!\nI am VAST Attendance bot. I will get all your subjects\' attendance details easily!\n\n'
        'Source Code : https://github.com/FOSSersVAST/vaasu\n\n'
        'Follow us on telegram : @FOSSersVAST\n\n'
        'Setup this bot : /login\n'
        'Get attendance : /attendance',
        reply_markup=ReplyKeyboardRemove())

    return


def login(update, context):
    user = update.message.from_user
    telegram_id = user.id
    if libvaasu.check(telegram_id):
        update.message.reply_text(
            'We care about your privacy. So, we encrypt your password before storing it in our database.\n\nNow please tell me your ERP username',
            reply_markup=ReplyKeyboardRemove()
        )

        return GET_ERP_USERNAME
    else:
        update.message.reply_text('You have already registered, try using /attendance')
        return ConversationHandler.END


def get_erpusername(update, context):
    user = update.message.from_user
    msg = update.message.text
    logger.info("User %s started the bot.", user.first_name)
    temp['erpusernames'][user.id] = msg
    update.message.reply_text("Okay, now tell me your ERP password: ")

    return GET_ERP_PASSWORD


def get_erppassword(update, context):
    user = update.message.from_user
    msg = update.message.text
    erpusername = temp['erpusernames'][user.id]
    user = update.message.from_user
    telegram_id = user.id

    login = libvaasu.login(erpusername, msg)
    if login == 'wrong':
        update.message.reply_text('Username or password is wrong! Try again : /login')
    else:
        if libvaasu.add_student(erpusername, msg, telegram_id):
            update.message.reply_text('Registration successful. Now you can use Vaasu bot. Use /attendance to get your attendance\n')
        else:
           update.message.reply_text('You have already registered an account, use /attendance')

    # /start conversation has ended
    return ConversationHandler.END


def logout(update, context):
    user = update.message.from_user
    telegram_id = user.id
    update.message.reply_text(
        'This bot is created by @fossersvast.'
        'Show some love when you see us ❤. May be with some treat.😊'
        'Bye! I hope we can meet again at Iraani.',
        reply_markup=ReplyKeyboardRemove())
    libvaasu.delete_from_table(telegram_id)
    return ConversationHandler.END


def stop(update, context):
    user = update.message.from_user
    logger.info("User %s stop its working...", user.first_name)
    update.message.reply_text(
        'This bot is created by @fossersvast.'
        'Show some love when you see us ❤. May be with some treat. 😊'
        'Bye! I hope we can meet again at Iraani. 😉',
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def getattendance(update, context):
    user = update.message.from_user
    telegram_id = user.id
    if libvaasu.check(telegram_id):
        update.message.reply_text("It seems you have not registered yet. Register with /login")
    else:
        update.message.reply_text("Checking the attendance, This may take some time")
        Attendance = libvaasu.get_attendance(telegram_id)
        if Attendance=={}:
            update.message.reply_text("Seems like there is some issues with the website!")
        elif Attendance:
            new_Attendance = ""
            for i,j in Attendance.items():
                new_Attendance += i + " - " + str(j) + "%\n\n"
            update.message.reply_text(new_Attendance)
    # else:
    #     update.message.reply_text("It seems you have not registered yet. Register with /login")
    return ConversationHandler.END


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    # Creates table in the database
    libvaasu.create_table()

    updater = Updater(os.getenv('BOT_TOKEN'),use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login)],

        states={
            GET_ERP_USERNAME: [MessageHandler(Filters.text, get_erpusername)],

            GET_ERP_PASSWORD: [MessageHandler(Filters.text, get_erppassword)],

        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("attendance",getattendance))
    dp.add_handler(CommandHandler("logout",logout))
    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
