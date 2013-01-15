from django import template

register = template.Library()


@register.inclusion_tag('pinpoint/snippets/youtube_video.html')
def youtube_video(video):
    return {'video': video}


@register.inclusion_tag('pinpoint/snippets/youtube_embed.html')
def embed_youtube_video(video, **kwargs):
    autoplay = kwargs.get('autoplay', False)
    width  = kwargs.get('width', 0)
    height = kwargs.get('height', 0)

    return {
        'video': video,
        'autoplay': autoplay,
        'width': width,
        'height': height,
    }


@register.inclusion_tag('pinpoint/snippets/youtube_image.html')
def youtube_image(video):
    return {'video': video, 'image_id': 0}
