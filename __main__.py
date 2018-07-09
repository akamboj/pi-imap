import os
import sys
import imaplib
import email
import email.header
import time
import subprocess

import getpass
import ConfigParser


# https://gist.github.com/robulouski/7441883

UPDATE_INTERVAL_SECS = 1.0
REFRESH_LOGIN_INTERVAL_SECS = 3600
OK_RV = 'OK'


COMMAND_WORD = 'COMMAND'
COMMAND_LIST = ['TurnOnPC']
COMMANDS = {
    'TurnOnPC' : {
        'script' : './TurnOnPC.sh'
    }
}

CONFIG_FILE_NAME = 'Config.cfg'
CONFIG_SECTION = 'General'



CONFIG_KEY_EMAIL_ACCOUNT = 'Email'
CONFIG_EMAIL_ACCOUNT = ''

CONFIG_KEY_EMAIL_PASSWORD = 'Password'
CONFIG_EMAIL_PASSWORD = ''

CONFIG_KEY_TRUSTED_ADDRESSES = 'TrustedAddresses'
CONFIG_TRUSTED_ADDRESSES = []

def main():
    # Set working to dir to this folder
    dir_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_path)


    read_config()

    log('Initial login')
    mailbox = login()
    
    startTime = time.time()
    while True:
        currentTime = time.time()
        # Refresh our login credntials every once in a while
        if currentTime - startTime > REFRESH_LOGIN_INTERVAL_SECS:
            log('Refreshing login')
            mailbox = login()

        rv, data = mailbox.select('INBOX')
        if rv != OK_RV:
            log('Error: got return value of (%s) when trying to select \'INBOX\'' % (rv))

        process_mailbox(mailbox)
        time.sleep(UPDATE_INTERVAL_SECS - ((time.time() - startTime) % UPDATE_INTERVAL_SECS))
    

def log(str):
    print str

def read_config():
    global CONFIG_EMAIL_ACCOUNT, CONFIG_EMAIL_PASSWORD, CONFIG_TRUSTED_ADDRESSES

    config = ConfigParser.ConfigParser()
    
    res = config.read(CONFIG_FILE_NAME)
    foundConfig = len(res) > 0

    if foundConfig != True:
        log("Config not found")
        # The config file doesn't exist, so make it
        config.add_section(CONFIG_SECTION)
        config.set(CONFIG_SECTION, CONFIG_KEY_EMAIL_ACCOUNT, '')
        config.set(CONFIG_SECTION, CONFIG_KEY_EMAIL_PASSWORD, '')
        config.set(CONFIG_SECTION, CONFIG_KEY_TRUSTED_ADDRESSES, '')

        with open(CONFIG_FILE_NAME, 'wb') as configfile:
            config.write(configfile)
            log("Wrote config file to " + CONFIG_FILE_NAME)
    else:
        log("Config found")
        CONFIG_EMAIL_ACCOUNT = config.get(CONFIG_SECTION, CONFIG_KEY_EMAIL_ACCOUNT)
        CONFIG_EMAIL_PASSWORD = config.get(CONFIG_SECTION, CONFIG_KEY_EMAIL_PASSWORD)
        
        addressList = config.get(CONFIG_SECTION, CONFIG_KEY_TRUSTED_ADDRESSES)
        # Clean up address strings
        for item in addressList.split(','):
            cleanedAddress = item.replace(' ', '').replace('\'', '').replace('\"', '')
            CONFIG_TRUSTED_ADDRESSES.append(cleanedAddress)

def login():
    mailbox = imaplib.IMAP4_SSL('imap.gmail.com')
    rv, data = mailbox.login(CONFIG_EMAIL_ACCOUNT, CONFIG_EMAIL_PASSWORD)
    if rv != OK_RV:
        log("Logging in returned (%s)" % (rv))
    return mailbox

def process_mailbox(mailbox):
    
    rv, results = mailbox.search(None, "ALL")

    for num in results[0].split():
        rv, data = mailbox.fetch(num, '(RFC822)')
        if rv != OK_RV:
            log('ERROR getting message %d' % (num))
            return

        msg = email.message_from_string(data[0][1])
        decode = email.header.decode_header(msg['Subject'])[0]
        subject = unicode(decode[0])

        decode = email.header.decode_header(msg['From'])[0]
        sender = unicode(decode[0])
        sender = email.utils.parseaddr(sender)

        if len(sender) == 1:
            senderEmail = sender[0]
        elif len(sender) == 2:
            senderEmail = sender[1]
        

        validationSucceeded, msg = validate_message(senderEmail, subject)
        if validationSucceeded == True:
            log('Processing (%s) from (%s)' % (msg, senderEmail))
            process_command(msg)
        else:
            log('Invalid email!\nSender: %s\nSubject: %s' % (senderEmail, subject))
            

        
        mailbox.store(num, '+FLAGS', '\\Deleted')
        log('Archived email')




# Return a tuple. 1st param, True if validation succeeded, if True, the 2nd param is the Command, if not it's why the validation failed
def validate_message(sender, subject):
    if sender not in CONFIG_TRUSTED_ADDRESSES:
        return False, ''

    # Split the command word and the actual command from the subject
    # We assume subjects take the form "'COMMAND_WORD'-'COMMAND'"
    splitSubject = subject.split('-')

    # Due to the above, our subjects should have len of 2 after splitting
    if len(splitSubject) != 2:
        return False, ''
    if splitSubject[0] != COMMAND_WORD:
        return False, ''

    requestedCommand = splitSubject[1]
    if requestedCommand not in COMMANDS:
        return FALSE, ''

    return True, requestedCommand


def process_command(command):
    scriptName = COMMANDS[command]['script']
    try:
        subprocess.call([scriptName])
    except WindowsError as e:
        log("Error: " + e.strerror)


if __name__ == "__main__":
    main()
