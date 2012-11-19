import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.contrib.contenttypes.models import ContentType

from apps.pinpoint.models import Campaign, BlockType, BlockContent
from apps.assets.models import Store, Product, YoutubeVideo, InstagramContent

import apps.pinpoint.wizards as wizards


@login_required
def login_redirect(request):
    store_set = request.user.store_set
    if store_set.count() == 1:
        return redirect('store-admin', store_id=str(store_set.all()[0].id))
    else:
        return redirect('admin')


@login_required
def admin(request):
    return render_to_response('pinpoint/admin_staff.html', {
        "stores": request.user.store_set
    }, context_instance=RequestContext(request))


@login_required
def store_admin(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    if not request.user in store.staff.all():
        raise Http404

    return render_to_response('pinpoint/admin_store.html', {
        "store": store
    }, context_instance=RequestContext(request))


@login_required
def new_campaign(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    return render_to_response('pinpoint/admin_new_campaign.html', {
        "store": store,
        "block_types": filter(lambda x: bool(x.image), BlockType.objects.all()),
    }, context_instance=RequestContext(request))


@login_required
def edit_campaign(request, store_id, campaign_id):
    store = get_object_or_404(Store, pk=store_id)
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    block_type = campaign_instance.content_blocks.all()[0].block_type

    return getattr(wizards, block_type.handler)(
        request, store, block_type, campaign=campaign_instance)


@login_required
def block_type_router(request, store_id, block_type_id):
    store = get_object_or_404(Store, pk=store_id)
    block_type = get_object_or_404(BlockType, pk=block_type_id)

    return getattr(wizards, block_type.handler)(request, store, block_type)


@login_required
def campaign_analytics_admin(request, campaign_id):
    pass


@login_required
def store_analytics_admin(request, store_id):
    pass


def campaign(request, campaign_id):
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)

    discovery_block_type = BlockType.objects.get(name__exact="Discovery Block")
    discovery_blocks = map(lambda x: BlockContent(block_type=discovery_block_type,
                                                  content_type=Product,
                                                  data=x),
                           campaign_instance.store.product_set.all())

    instagram_block = BlockType.objects.get(name__exact="Discovery Instagram Block")
    #instagram_content = InstagramContent.objects.all()[2]
    #content = BlockContent(block_type=instagram_block,
    #                       content_type=InstagramContent,
    #                       data=instagram_content)
    #discovery_blocks.append(content)

    #instagram_content = InstagramContent.objects.all()[0]
    #content = BlockContent(block_type=instagram_block,
    #                       content_type=InstagramContent,
    #                       data=instagram_content)
    #discovery_blocks.insert(3, content)

    #instagram_content = InstagramContent.objects.all()[1]
    #content = BlockContent(block_type=instagram_block,
    #                       content_type=InstagramContent,
    #                       data=instagram_content)
    #discovery_blocks.insert(5, content)

    instagram_contents = InstagramContent.objects.all()
    for ic in instagram_contents:
        content = BlockContent(block_type=instagram_block,
                               content_type=InstagramContent,
                               data=ic)
        discovery_blocks.insert(random.randrange(len(instagram_contents)), content)

    youtube_video = YoutubeVideo.objects.all()[0]
    video_type = BlockType.objects.get(name__exact="Discovery Youtube Video Block")
    video = BlockContent(block_type=video_type,
                         content_type=YoutubeVideo,
                         data=youtube_video)
    discovery_blocks.insert(0, video)

    return render_to_response('pinpoint/campaign.html', {
        "campaign": campaign_instance,
        "columns": range(4),
        "preview": not campaign_instance.live,
        "discovery_blocks": discovery_blocks,
    }, context_instance=RequestContext(request))
