import os
import sys
import imaplib
import email
import email.header
import subprocess

import getpass
import ConfigParser


# https://gist.github.com/robulouski/7441883

OK_RV = 'OK'
COMMAND_WORD = 'COMMAND'
COMMAND_LIST = ['TurnOnPC']
COMMANDS = {
    'TurnOnPC' : {
        'script' : './TurnOnPC.sh'
    }
}

CONFIG_TRUSTED_ADDRESSES = ['rpi.akamboj@gmail.com', 'akamboj2000@gmail.com']
CONFIG_EMAIL_ACCOUNT = 'rpi.akamboj@gmail.com'
CONFIG_EMAIL_PASSWORD = 'Byibgifvutwac67'

def main():
    read_config()
    # Set working to dir to this folder
    dir_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_path)

    mailbox = imaplib.IMAP4_SSL('imap.gmail.com')

    rv, data = mailbox.login(CONFIG_EMAIL_ACCOUNT, CONFIG_EMAIL_PASSWORD)
    rv, list = mailbox.list()
    print list

    rv, data = mailbox.select('INBOX')
    process_mailbox(mailbox)
    pass

def log(str):
    print str

def read_config():
    pass

def process_mailbox(mailbox):
    
    rv, results = mailbox.search(None, "ALL")

    for num in results[0].split():
        rv, data = mailbox.fetch(num, '(RFC822)')
        if rv != OK_RV:
            print "ERROR getting message", num
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
        

        print 'Message %s: %s' % (num, subject)

        validationSucceeded, msg = validate_message(senderEmail, subject)
        if validationSucceeded == True:
            
            process_command(msg)
            pass
        else:
            log('Invalid email!\nSender: %s\nSubject: %s' % (senderEmail, subject))
            

        
        # mailbox.store(num, '+FLAGS', '\\Deleted')

    # Not sure if we need to actually expunge
    # mailbox.expunge()


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
    log('Running (%s) in dir (%s)' % (scriptName, os.getcwd()))
    subprocess.call([scriptName])


if __name__ == "__main__":
    main()
