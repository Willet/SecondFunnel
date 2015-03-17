#   Library docs: https://github.com/iktakahiro/slackpy
#   Slack API docs: https://api.slack.com/incoming-webhooks
import slackpy as slack


INCOMING_WEB_HOOK = "https://hooks.slack.com/services/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"


def msg(channel, sender, message, level="info"):
    if level not in ['info','warn','error']:
        level = 'info'
    s = slack.SlackLogger(INCOMING_WEB_HOOK, channel, sender)
    getattr(s, level)(message=message)