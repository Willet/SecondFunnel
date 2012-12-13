from django import template

register = template.Library()


@register.inclusion_tag('pinpoint/snippets/youtube_video.html')
def youtube_video(video):
    return {'video': video}


@register.inclusion_tag('pinpoint/snippets/youtube_embed.html')
def embed_youtube_video(video, autoplay=False):
    return {'video': video, 'autoplay': autoplay}


@register.inclusion_tag('pinpoint/snippets/youtube_image.html')
def youtube_image(video):
    return {'video': video, 'image_id': 0}
