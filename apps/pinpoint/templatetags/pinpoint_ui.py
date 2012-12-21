from django import template
from django.conf import settings
from django.db.models import Q
from django.template.loader import render_to_string
from django.template import Context
from django.utils.html import escape
from django.template.loader_tags import do_include

from apps.pinpoint.models import BlockContent

register = template.Library()


@register.inclusion_tag('pinpoint/snippets/field_label_value.html')
def ui_field_label_value(label, value):
    return {'label': label, 'value': value}


class ConfirmCampaignNode(template.Node):
    """
    Renders a confirmation page of a wizard.

    @deprecated: We no longer have a confirmation page.
    """
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
    """
    Renders a confirmation page of a wizard.

    @deprecated: We no longer have a confirmation page.
    """
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, campaign = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return ConfirmCampaignNode(campaign)


class BlockNode(template.Node):
    """
    Renders a content block.

    @deprecated: We now render blocks using themes.
    """
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
    """
    Renders a content block.

    @deprecated: We now render blocks using themes.
    """
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, ui_block = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return BlockNode(ui_block)


@register.inclusion_tag('pinpoint/snippets/social_buttons.html')
def social_buttons(product, count=None):
    """Renders social buttons."""
    if hasattr(product, 'is_featured') and product.is_featured:
        featured = True
        image = product.featured_image
    else:
        featured = False
        images = product.media.all()
        if images:
            image = images[0].get_url()
        else:
            image = None

    # Explicit settings override convention
    if count is None and featured:
        count = True
    elif count is None:
        count = False

    url = product.original_url

    return {
        'featured': featured,
        'url': url,
        'image': image,
        'count': count
    }


class IncludeEscNode(template.Node):
    """Renders a template with the contents excaped."""
    def __init__(self, parser, token):
        self.parser = parser
        self.token = token

    def render(self, context):
        parser = self.parser
        token = self.token

        return escape(do_include(parser, token).render(context))


@register.tag(name="include_escaped")
def include_escaped(parser, token):
    """Renders a template with the contents excaped."""
    return IncludeEscNode(parser, token)
