import re

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

    return {
        'featured': featured,
        'url'     : product.original_url,
        'image'   : image,
        'count'   : count,
        'name'    : product.name,
        'brand'   : product.store.name
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


@register.filter(name='size')
def size(value, arg):
    if not value:
        return value

    if value.endswith('.gif'):
        return value

    return value.replace("master.jpg", "{0}.jpg".format(arg))


@register.simple_tag
def extract_style(some_string):
    """Returns the sum of non-inline CSS included in the HTML string."""
    styles = re.findall('<style[^>]*>([^<]*)</style>', some_string,
                        re.MULTILINE)
    return ';\n'.join(styles)