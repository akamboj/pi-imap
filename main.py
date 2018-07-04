import os
import sys
import imaplib
import email
import email.header
import getpass

# https://gist.github.com/robulouski/7441883

OK_RV = 'OK'
COMMAND_WORD = 'COMMAND'

EMAIL_ACCOUNT = "rpi.akamboj@gmail.com"

CONFIG_TRUSTED_ADDRESSES = ['']

def main():
    mailbox = imaplib.IMAP4_SSL('imap.gmail.com')

    rv, data = mailbox.login(EMAIL_ACCOUNT, "Arag0rn13")
    rv, list = mailbox.list()
    print list

    rv, data = mailbox.select('INBOX')
    process_mailbox(mailbox)
    pass

def log(str):
    print str

def process_mailbox(mailbox):
    
    rv, results = mailbox.search(None, "ALL")

    for num in results[0].split():
        rv, data = mailbox.fetch(num, '(RFC822)')
        if rv != 'OK':
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

        if validate_message(senderEmail, subject) == True:
            
            command = get_command_from_subject(subject)
            process_command(command)
            pass
        else:
            log('Invalid email!\nSender: %s\nSubject: %s' % (senderEmail, subject))
            

        


    pass

def validate_message(sender, subject):
    if sender not in CONFIG_TRUSTED_ADDRESSES:
        return False

    # Split the command word and the actual command from the subject
    # We assume subjects take the form "'COMMAND_WORD'-'COMMAND'"
    splitSubject = subject.split('-')

    # Due to the above our subjects should have len of 2 after splitting
    if len(splitSubject) != 2:
        return False
    if splitSubject[0] != COMMAND_WORD:
        return False

    COMMAND_LIST = ['']
    if splitSubject[1] not in COMMAND_LIST:
        return False

    return True, splitSubject[1]

def get_command_from_subject():
    return ''

def process_command(command):
    pass

if __name__ == "__main__":
    main()
