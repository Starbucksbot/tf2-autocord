from gevent.monkey import patch_socket, patch_ssl
patch_socket()
patch_ssl()
from steam.enums import EResult
from steam.client import SteamClient

import json
import discord

from discord.ext import commands
from sys import stderr
from traceback import print_exc
from threading import Thread
from os import listdir
from os.path import isfile, join


preferences = json.loads(open('Login details/preferences.json', 'r').read())
command_prefix = preferences["Command Prefix"]
login = json.loads(open('Login details/sensitive details.json', 'r').read())
token = login["Bot Token"]

bot = commands.Bot(command_prefix=commands.when_mentioned_or(command_prefix), case_insensitive=True,
                   description='Used to manage your tf2automatic bot and send all of Steam messages through Discord')
bot.remove_command('help')
bot.cli_login = True

# cogs -----------------------------------------------------------------------------------------------------------------

bot.initial_extensions = [f.replace('.py', '') for f in listdir("Cogs") if isfile(join("Cogs", f))]  # getting the cog
# files in the "Cogs" folder and removing the none .py ones

if __name__ == '__main__':
    print(f'Extensions to be loaded are {bot.initial_extensions}')
    for extension in bot.initial_extensions:
        try:
            bot.load_extension(f'Cogs.{extension}')
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.', file=stderr)
            print_exc()

# threading ------------------------------------------------------------------------------------------------------------

def discordside():
    print('\033[95m' + '-' * 30 + '\033[95m')
    print('\033[95m' + 'Discord is logging on' + '\033[95m')
    while 1:
        bot.run(token)


def steamside():
    while 1:
        if bot.dsdone is True:
            bot.client = SteamClient()
            print('\033[95m' + '-' * 30 + '\033[95m')
            print('\033[95m' + 'Steam is now logging on' + '\033[95m')
            bot.client.set_credential_location('Login Details/')  # where to store sentry files and other stuff  

            @bot.client.on('error')
            def handle_error(result):
                print('\033[91m' + f'Logon result: {repr(result)}' + '\033[91m')

            @bot.client.on('connected')
            def handle_connected():
                print('\033[92m' + f'Connected to: {bot.client.current_server_addr}' + '\033[92m')

            @bot.client.on('reconnect')
            def handle_reconnect(delay):
                print('\033[94m' + f'Reconnect in {delay}...' + '\033[94m')

            @bot.client.on('disconnected')
            def handle_disconnect():
                print('\033[93m' + 'Disconnected.' + '\033[93m')

                if bot.client.relogin_available:
                    print('Reconnecting...')
                    bot.client.reconnect(maxdelay=30)

            @bot.client.on('logged_on')
            def handle_after_logon():
                bot.logged_on = True
                print('\033[92m' + f'Logged on as: {bot.client.user.name}' + '\033[92m')

            @bot.client.on('chat_message')
            def handle_message(user, message_text):
                if user.steam_id == bot.bot64id:
                    if 'view it here' not in message_text and 'marked as declined' in message_text:
                        bot.trades += 1
                    else:
                        if 'from user' in message_text:
                            bot.usermessage = message_text
                        if bot.currenttime == '23:59' and "You've made" in message_text:
                            bot.graphplots = message_text
                        else:
                            bot.sbotresp = message_text

            result = bot.client.cli_login(username=bot.username, password=bot.password)
            if result != EResult.OK:
                print('\033[91m' + f'Failed to login: {repr(result)}' + '\033[91m')
                raise SystemExit
            while 1:
                bot.client.run_forever()


Thread(target=discordside).start()
Thread(target=steamside).start()
