# bot.py
# Christopher O'Neal
#
# A simple IRC bot made to play around with Markov chains.
#


import socket, string, time, random, collections

class bot:
    responses = {}
    permissions = {}
    settings = {'host': '',
                'port': '',
                'pw': '',
                'nick': '',
                'ident': '',
                'channel':'',
                'markov': '',
                'chainlength': '',
                'chattiness': '',
                'logging': '',
                }
    markov = dict()
    SETTINGS_FILE = 'settings.txt'
    RESPONSES_FILE = 'responses.txt' 
    PERMISSIONS_FILE = 'permissions.txt'
    MARKOV_FILE = 'markov_brain.txt'
    STOP_WORD = '\n'
    START_KEY = STOP_WORD, STOP_WORD
    
    # bot.init - Loads settings, responses and creates markov brain
    #
    #
    def __init__(self):
       self.loadSettings()
       self.loadResponses()
       if self.settings['markov'] == '1':
           self.loadMarkovBrain()
       self.socket = socket.socket()
      
    # bot.loadSettings - Loads settings from text file
    #
    #    
    def loadSettings(self):
        loadFile = open(SETTINGS_FILE, 'r')
        for line in loadFile:
            line = line.strip()
            settingLine = line.split('=')
            if settingLine[0] in self.settings:
                if (settingLine[0] == 'port') or (settingLine[0] == 'chainlength'):
                    try:
                        self.settings[settingLine[0]] = int(settingLine[1])
                    except:
                        self.settings[settingLine[0]] = 6667
                elif settingLine[0] == 'chattiness':
                   try:
                        self.settings[settingLine[0]] = float(settingLine[1])
                   except:
                        self.settings[settingLine[0]] = 0.03
                else:
                    self.settings[settingLine[0]] = settingLine[1]
        loadFile.close()
    
    # bot.connect - Connects to the specified host, identifies the bot using 
    #               saved settings.
    #            
    def connect(self):
        self.socket.connect((self.settings['host'], self.settings['port']))
        time.sleep(0.2)
        self.socket.send('NICK %s\r\n' % self.settings['nick'])
        time.sleep(0.2)
        self.socket.send('USER %s %s blah :%s\r\n' % (self.settings['ident'], self.settings['host'], self.settings['nick']))
        time.sleep(0.2)
        self.join(self.settings['channel'])
        time.sleep(0.2)
        self.identify

    # bot.disconnect - Disconnects from host and exits program
    #
    #    
    def disconnect(self):
        print "Quitting..."
        self.socket.send("QUIT\r\n")
        exit()
    
    # bot.join - Joins specified channel
    #
    #    
    def join(self, channel):
        print "==&gt: Joining %s" % channel
        self.socket.send("JOIN %s\r\n" % channel)
    
    # bot.leave - Leaves specified channel
    #
    #    
    def leave(self, channel, message = "~~~"):
        self.socket.send('PART %s :%s\r\n' %(channel, message))
    
    # bot.pong - Responds to automatic messages from host
    #
    #    
    def pong(self, data):
        self.socket.send('PONG %s\r\n' % data)
    
    # bot.handleMessage - Handles messages that are received from host
    #                     If message isn't a ~ command, add the text to the brain
    #    
    def handleMessage(self, channel, nick, message):
        print '%s on %s: %s' % (nick, channel, message)
        if (message[0] == '~'):
            print 'command=&gt;'
            dat = message.split()
            self.handleCommand(channel, nick, dat[0], dat[1:])
        else:
            self.addToBrain(message, self.settings['chainlength'], writeToFile = True)
            if self.settings['markov'] == '1':
                if random.random() <= self.settings['chattiness']:
                    sentence = self.generateSentence(message, self.settings['chainlength'])
                    if sentence and sentence != message:
                        self.reply(channel, '', sentence)
    
    # bot.addResponse - Add user defined response
    #
    #    
    def addResponse(self, command, response):
        self.responses[command] = ' '.join(response)
        self.saveResponses()
        
    # bot.loadResponses - Load user defined responses from file
    #
    #    
    def loadResponses(self):
        loadFile = open(RESPONSES_FILE, 'r')
        self.responses = eval(loadFile.read())
        loadFile.close()
    
    # bot.saveResponses - Save user defined responses to file
    #
    #    
    def saveResponses(self):
        writeFile = open(RESPONSES_FILE, 'r')
        writeFile.write(str(self.responses))
        writeFile.close()
    
    # bot.addPermission - Add user permission level
    #                     (permission levels not yet implemented fully)
    #    
    def addPermission(self, nick, level):
        self.permissions[nick] = ' '.join(level)
        self.savePermissions()
    
    # bot.loadPermissions - Load user permission levels from file
    #
    #    
    def loadPermissions(self):
        loadFile = open(PERMISSIONS_FILE, 'r')
        self.permissions = eval(loadFile.read())
        loadFile.close()
    
    # bot.savePermissions - Save user permission levels to file
    #
    #    
    def savePermissions(self):
        writeFile = open(PERMISSIONS_FILE, 'w')
        writeFile.write(str(self.permissions))
        writeFile.close()
    
    # bot.handleCommand - Handles ~ commands
    #
    #    
    def handleCommand(self, channel, nick, command, arguments):
        command = command[1:]
        {'die': lambda: self.disconnect(),
         'join': lambda: self.join(), 
         'leave': lambda: self.leave(channel),
         'identify': lambda: self.identify(),
         'define': lambda: self.addResponse(arguments[0], arguments[1:]),
         'setlevel': lambda: self.addPermission(arguments[0], arguments[1:]), 
         'chat': lambda: self.chat(arguments)
         }.get(command, self.checkResponses(command, nick))()
    
    # bot.chat - Chats using the markov chat logic
    #
    #      
    def chat(self, arguments):
        if self.settings['markov'] == 1:
            if len(arguments):
                if arguments[0] == 'about':
                    chatString = ' '.join(arguments[1:])
                    stringLength = len(chatString.split())
                    sentence = self.generateSentence(chatString, random.randint(stringLength, (stringLength + 20)))
                    if sentence == chatString:
                        sentence = 'I can\'t D:'
                        print sentence
                        self.reply(channel, '', sentence)
                else:
                    sentence = self.generateSentence('', random.randint(1, 30))
                    print sentence
                    self.reply(channel, '', sentence)
    
    # bot.checkResponses - Checks to see if the command is a user defined response
    #                      If so, returns the appropriate response
    #                
    def checkResponses(self, command, nick):
        if command in self.responses:
            self.reply(channel, nick, self.responses[command])
    
    # bot.reply - General logic to send message to channel
    #
    #    
    def reply(self, channel, nick, message):
        self.socket.send('PRIVMSG %s %s:%s\r\n' % (channel, nick, message))
    
    # bot.flush - Flush socket buffer
    #
    #    
    def flush(self):
        print self.socket.recv(4096)
        
    # bot.identify - Identifies bot to host
    #
    #
    def identify(self):
        self.reply('NickServ', '', 'IDENTIFY %s' % self.settings['pw'])
    
    # bot.loadMarkovBrain - Loads markov file, adds to brain
    #
    #
    def loadMarkovBrain(self):
        openFile = open(MARKOV_FILE, 'r')
        for line in openFile:
            self.addToBrain(line, self.settings['chainlength'])
    
    # bot.addToBrain - Adds chat info to brain
    #                  Also handles adding chat info to markov file
    #
    def addToBrain(self, msg, chainLength = 2, writeToFile = False):
        if writeToFile:
            writeFile = open(MARKOV_FILE, 'a')
            writeFile.write(msg + '\n')
            writeFile.close()
        word1, word2 = self.START_KEY
        for word3 in msg.split():
            self.markov.setdefault((word1, word2), list()).append(word3)
            word1, word2 = word2, word3
        self.markov.setdefault((word1, word2), list()).append(self.STOP_WORD) 
    
    # bot.generateSentence - Randomly generates a sentence using markov logic
    #
    #    
    def generateSentence(self, msg, chainLength, maxWords = 10000):
        output = list()
        words = msg.split()
        messageLength = len(words)
        word1, word2 = self.START_KEY
        if messageLength > chainLength:
            for i in xrange(chainLength):
                word3 = words[i]
                output.append(word3)
                word1, word2 = word2, word3
        else:
            for i in xrange(messageLength):
                word3 = words[i]
                output.append(word3)
                word1, word2 = word2, word3
        for i in xrange(maxWords):
            try:
                word3 = random.choice(self.markov[(word1, word2)])
            except (IndexError, KeyError):
                continue
            if word3 == self.STOP_WORD:
                break
            output.append(word3)
            word1, word2 = word2, word3
        return ' '.join(output)
    
    # bot.mainloop - Main logic loop.  Gets messages and processes
    #
    #    
    def mainloop(self):
        readbuffer = ''
        while 1:
            data = self.socket.recv(1024)
            if data:
                print data
                readbuffer = readbuffer + data
                temp = string.split(readbuffer, '\n')
                readbuffer = temp.pop()
                for line in temp:
                    line = line.rstrip()
                    line = line.split()
                    print "line ##'%s'##" % line
                    if line [0] == 'PING':
                        self.pong(line[1])
                    else:
                        if line [1] == 'PRIVMSG':
                            channel = line[2]
                            nick = line[0].split('~')[0]
                            message = ' '.join(line[3:])[1:]
                            self.handleMessage(channel, nick, message)