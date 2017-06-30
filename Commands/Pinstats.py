import botconfig
import re
import datetime
from datetime import timedelta
from Models.Command import Command


class Pinstats(Command):
    def __init__(self, client, command_head, command_text, channel):
        Command.__init__(self, client, command_head, command_text, channel)
        self.channel = None
        self.date = None
        self.command = None

    def parse_arguments(self):
        date = None
        channel = None
        command = None
        command_text = self.COMMAND_TEXT
        date_pattern = re.compile("(today)|(yesterday)|([0-9]{1,2}/[0-9]{1,2}(/[0-9]{2})?)")
        channel_pattern = re.compile("<#[a-zA-Z0-9]*\|[0-9]+[a-zA-Z_]*>")
        command_pattern = re.compile("(users)|(channels)|(words)")

        if command_text.count(' ') == 0:
            if date_pattern.match(command_text.split(' ')[0]):
                date = command_text.split(' ')[0]
                channel = self.CHANNEL
            elif channel_pattern.match(command_text.split(' ')[0]):
                # date = datetime.datetime.today().strftime("%m/%d/%y")
                channel = command_text.split('#')[1].split('|')[0]
            elif command_pattern.match(command_text.split(' ')[0]):
                command = command_text.split(' ')[0]

        elif command_text.count(' ') == 1:
            if channel_pattern.match(command_text.split(' ')[0]) and date_pattern.match(command_text.split(' ')[1]):
                channel = command_text.split('#')[1].split('|')[0]
                date = command_text.split(' ')[1]

        if date is not None:
            if date == 'today':
                date = datetime.datetime.today().strftime("%m/%d/%y")
            elif date == 'yesterday':
                date = datetime.datetime.today() - timedelta(days=1)
                date = date.strftime("%m/%d/%y")

        self.channel = channel.upper()
        self.date = date
        self.command = command

    def execute_command(self):
        slack_client = self.CLIENT
        token = botconfig.SLACK_BOT_TOKEN

        self.parse_arguments()

        if self.command is None:
            self.pinstats()
            print("no command - pulling back stats for a specific channel")

    def pinstats(self):
        slack_client = self.CLIENT
        token = botconfig.SLACK_BOT_TOKEN

        # Grab the list of pins for this channel from the Slack API
        pins_json = slack_client.api_call("pins.list", token=token, channel=self.channel)
        pins_list = pins_json['items']

        pin_counts = dict()
        pinner_counts = dict()
        for pin in pins_list:
            pin_type = pin['type']
            if pin[pin_type]['user'] not in pin_counts.keys():
                pin_counts[pin[pin_type]['user']] = 0
            pin_counts[pin[pin_type]['user']] += 1

            if pin['created_by'] not in pinner_counts.keys():
                pinner_counts[pin['created_by']] = 0
            pinner_counts[pin['created_by']] += 1
        print("pins in channel: {0}".format(len(pins_list)))
        print("pin_counts: {0}".format(pin_counts))
        print("pinner_counts: {0}".format(pinner_counts))
        attachment = list()
        i = 0
        header = {
            'text': "Users with top # of messages for the channel:\n"
        }
        attachment.append(header)
        for user_id in sorted(pin_counts, key=pin_counts.get, reverse=True):
            i += 1
            user_json = slack_client.api_call("users.info", token=token, user=user_id)
            user = user_json['user']
            poster = user['profile']
            print("{0} {1}".format(user['name'], pin_counts[user_id]))

            entry = {
                'author_icon': poster['image_32'],
                'author_name': "{0}{1}{2}{3}{4}{5}".format(i, ". ", user['name'], ": ", pin_counts[user_id], " messages")
            }

            # Finally, append this pin object to the attachment array
            attachment.append(entry)
        slack_client.api_call('chat.postMessage',
                              channel=self.CHANNEL,
                              attachments=attachment,
                              as_user=True)
        attachment.clear()
        i = 0
        header = {
            'text': "Users with top # of pins for the channel:\n"
        }
        attachment.append(header)
        for user_id in sorted(pinner_counts, key=pinner_counts.get, reverse=True):
            i += 1
            user_json = slack_client.api_call("users.info", token=token, user=user_id)
            user = user_json['user']
            poster = user['profile']
            print("{0} {1}".format(user['name'], pinner_counts[user_id]))

            entry = {
                'author_icon': poster['image_32'],
                'author_name': "{0}{1}{2}{3}{4}{5}".format(i, ". ", user['name'], ": ", pinner_counts[user_id],
                                                           " pins")
            }

            # Finally, append this pin object to the attachment array
            attachment.append(entry)
        slack_client.api_call('chat.postMessage',
                              channel=self.CHANNEL,
                              attachments=attachment,
                              as_user=True)

