#!/usr/bin/env python3
# coding: utf-8
from telegram.ext import Updater, CommandHandler, RegexHandler, Filters
from telegram import ParseMode
from subprocess import run, CalledProcessError
import shlex, logging, json
from functools import wraps

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.DEBUG)

with open('settings.json') as f:
    settings = json.load(f)

LIST_OF_ADMINS = settings['admins']
YT-DL_PATH = settings['yt-dl_path']
DOWNLOADDIR = settings['downloaddir']

updater = Updater(settings['bot_token'])
job_queue = updater.job_queue


def restricted(func):
    @wraps(func)
    def wrapped(bot, update):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(bot, update)
    return wrapped


def starthelp(bot, update):
    update.message.reply_text(
        'Hello this bot is only for personal use and might not work for you.\
        If you\'re into IT, then check out the sourcecode: https://github.com/Thorbijoern/yt-dl_bot')

@restricted
def link(bot, update):
    update.message.reply_text('downloading...', quote=True)
    link = update.message.text
    message_id = update.message.message_id
    user_id = update.effective_user.id
    job_queue.run_once(download, 0, context={'link': link, 'message_id': message_id, 'user_id': user_id})
    

def download(bot, job):
    link = job.context['link']
    message_id = job.context['message_id']
    user_id = job.context['user_id']
    # beware shell injections! shlex.quote should escape them
    # and the regex of the regexhandler should exclude other stuff
    command = '{} -x --audio-format mp3 {}'.format(YT-DL_PATH, shlex.quote(link))
    try:
        result = run(command, shell=True, capture_output=True, check=True, cwd=DOWNLOADDIR)
        bot.send_message(
            user_id,
            'downloaded successfully',
            reply_to_message_id=message_id,
            quote=True)
    except CalledProcessError as err:
        bot.send_message(
            user_id,
            'process exited with code {}\n\n```{}```'.format(err.returncode, err.output),
            reply_to_message_id=message_id,
            quote=True,
            parse_mode=ParseMode.MARKDOWN)


def sorry(bot, update):
    update.message.reply_text('sorry, i can\'t use that', quote=True)


updater.dispatcher.add_handler(CommandHandler(['start', 'help'], starthelp))
regex = 'https?://(www\.)?youtu(\.)?be(\.com)?/(?(3)watch\?v=|)?(?!playlist)[a-zA-Z0-9\-_]{4,15}'
updater.dispatcher.add_handler(RegexHandler(regex, link))
#updater.dispatcher.add_handler(MessageHandler(Filters.all, sorry))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
