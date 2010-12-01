# main.py
# Christopher O'Neal
#
# Main loader program for IRC bot
#


import time
from bot import bot

if __name__ == '__main__':
    bot = bot()
    try:
        bot.connect()
        bot.flush()
        bot.mainloop()
    except:
        print "Interrupt"
        bot.disconnect()
        raise
    