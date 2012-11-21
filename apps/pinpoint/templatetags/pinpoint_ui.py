from django import template
from django.conf import settings
from django.db.models import Q
from django.template.loader import render_to_string
from django.template import Context

from apps.pinpoint.models import BlockContent

register = template.Library()


@register.inclusion_tag('pinpoint/snippets/field_label_value.html')
def ui_field_label_value(label, value):
    return {'label': label, 'value': value}


class ConfirmCampaignNode(template.Node):
    def __init__(self, campaign):
        self.campaign = template.Variable(campaign)

    def render(self, context):
        campaign = self.campaign.resolve(context)

        content_block = campaign.content_blocks.all()[0]

        return render_to_string("pinpoint/wizards/%s/confirm.html" % content_block.block_type.slug, {
            'content_block': content_block,
            'campaign': campaign
        })

@register.tag(name="wizard_confirm_campaign")
def wizard_confirm_campaign(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, campaign = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return ConfirmCampaignNode(campaign)


class BlockNode(template.Node):
    def __init__(self, ui_block, path=None):
        if path:
            self.template_path = template.Variable(path)
        else:
            self.template_path = None
        self.ui_block      = template.Variable(ui_block)

    def render(self, context):
        ui_block      = self.ui_block.resolve(context)

        if self.template_path:
            template_path = self.template_path.resolve(context)
        else:
            template_path = "pinpoint"

        return render_to_string([
            (template_path + "/ui_blocks/%s.html") % ui_block.block_type.slug,
            (template_path + "/ui_blocks/generic.html"),
        ], {
            'data': ui_block.data
        })

@register.tag(name="render_ui_block")
def render_ui_block(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tokens = token.split_contents()
        tag_name = tokens[0]
        ui_block = tokens[1]
        path     = tokens[2] if len(tokens) > 2 else None
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return BlockNode(ui_block, path)


class YoutubeVideoNode(template.Node):
    def __init__(self, yt_video, width, height):
        self.yt_video = template.Variable(yt_video)
        self.width = template.Variable(width)
        self.height = template.Variable(height)

    def render(self, context):
        yt_video = self.yt_video.resolve(context)
        width = self.width.resolve(context)
        height = self.height.resolve(context)

        return yt_video.embed(width, height)


@register.tag(name="youtube_embed")
def youtube_embed(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, yt_video, width, height = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return YoutubeVideoNode(yt_video, width, height)
