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
    def __init__(self, ui_block):
        self.ui_block = template.Variable(ui_block)

    def render(self, context):
        ui_block = self.ui_block.resolve(context)

        return render_to_string([
            "pinpoint/ui_blocks/%s.html" % ui_block.block_type.slug,
            "pinpoint/ui_blocks/generic.html",
        ], {
            'data': ui_block.data
        })

@register.tag(name="render_ui_block")
def render_ui_block(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, ui_block = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return BlockNode(ui_block)

@register.inclusion_tag('pinpoint/snippets/social_buttons.html')
def social_buttons(product, count=None):
    if hasattr(product, 'is_featured') and product.is_featured:
        featured = True
        image    = product.featured_image
    else:
        featured = False
        image    = product.media.all()[0].get_url()

    # Explicit settings override convention
    if count is None and featured:
        count = True
    elif count is None:
        count = False

    url = product.original_url

    return {
        'featured': featured,
        'url'     : url,
        'image'   : image,
        'count'   : count
    }