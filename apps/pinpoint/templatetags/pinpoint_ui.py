from django import template
from django.conf import settings
from django.db.models import Q
from django.template.loader import render_to_string
from django.template import Context

from apps.pinpoint.models import BlockContent

register = template.Library()


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
def get_unread_message_count(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, ui_block = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return BlockNode(ui_block)
