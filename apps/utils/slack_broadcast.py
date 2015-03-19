import os
import requests
import json
from argparse import ArgumentParser


INCOMING_WEB_HOOK = "https://hooks.slack.com/services/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"


def msg(channel, sender, title, message, level="info"):
    if level not in ['info','warn','error']:
        level = 'error'
    print message
    s = SlackLogger(INCOMING_WEB_HOOK, channel, sender)
    getattr(s, level)(message=message, title=title)



### SIMPLE SLACK WEBHOOKS API - by Takahiro Ikeuchi
#   Library docs: https://github.com/iktakahiro/slackpy
#   Slack API docs: https://api.slack.com/incoming-webhooks

class SlackLogger:
    def __init__(self, web_hook_url, channel, username='Logger'):

        self.web_hook_url = web_hook_url
        self.channel = channel
        self.username = username

    def __send_notification(self, message, title, color='good'):
        """Send a message to a channel.
        Args:
            title: The message title.
            message: The message body.
            color: Can either be one of 'good', 'warning', 'danger', or any hex color code

        Returns:
            api_response:

        Raises:
            TODO:
        """
        __fields = {
            "title": title,
            "text": message,
            "color": color,
            "fallback": title,
        }

        __attachments = {
            "fields": __fields
        }

        payload = {
            "channel": self.channel,
            "username": self.username,
            "attachments": __attachments
        }

        response = requests.post(self.web_hook_url, data=json.dumps(payload))

        return response

    def info(self, message, title='Slack Notification'):

        title = 'INFO : {0}'.format(title)
        return self.__send_notification(message=message, title=title, color='good')

    def warn(self, message, title='Slack Notification'):

        title = 'WARN : {0}'.format(title)
        return self.__send_notification(message=message, title=title, color='warning')

    def error(self, message, title='Slack Notification'):

        title = 'ERROR : {0}'.format(title)
        return self.__send_notification(message=message, title=title, color='danger')