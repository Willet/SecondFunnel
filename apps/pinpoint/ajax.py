from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.forms import ImageField, ValidationError
from django.views.decorators.http import require_POST

from apps.assets.models import GenericImage
from apps.pinpoint.models import Campaign
from apps.utils.ajax import ajax_success, ajax_error


@login_required
def campaign_save_draft(request):
    """
    Sets a campaign given by the the request to be inaccessable to the public.

    @deprecated: Pinpoint pages are now always live.

    @return: An HttpsResponse containing json with a success attribute.
    """
    return modify_campaign(request, False)


@login_required
def campaign_publish(request):
    """
    Sets a campaign given by the the request to be publicly accessable.

    @deprecated: Pinpoint pages are now always live.

    @param request: The request containing the campaign id.

    @return: An HttpsResponse containing json with a success attribute.
    """
    return modify_campaign(request, True)

@require_POST
def modify_campaign(request, live):
    """
    Sets a campaign's accessability given by the the request.

    @deprecated: Pinpoint pages are now always live.

    @param request: The request containing the campaign id.
    @param live: Whether the page should be live or not.

    @return: An HttpsResponse containing json with a success attribute.
    """
    campaign_id = request.POST.get('campaign_id')
    
    if not campaign_id:
        return ajax_error({'error': "Campaign ID doesn't exist."})

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return ajax_error({'error': "Campaign doesn't exist."})
    else:
        if not request.user in campaign.store.staff.all():
            return ajax_error({'error': "User is not staff for the given store."})

        campaign.live = live
        campaign.save()

    return ajax_success()


def upload_image(request):
    """
    Uploads an image given by the request.

    @param request: The request containing the image.

    @return: An HttpResponse object containing json.
    """
    # in IE this gets sent as a file
    if 'qqfile' in request.FILES:
        try:
            media = GenericImage()
            imgField = ImageField().clean(request.FILES['qqfile'], media)
            media.hosted.save(imgField.name, imgField)
            media.save()
        except (KeyError, ValidationError), e:
            raise e

    # in other browsers we read this using request.read
    else:
        # read file info from stream
        uploaded = request.read

        # get file size
        fileSize = int(uploaded.im_self.META.get("CONTENT_LENGTH", None))

        # get file name
        fileName = request.GET.get('qqfile', None)

        if None in (fileSize, fileName):
            return ajax_error({'error': "" + str(fileSize) + " or " + str(fileName) + " is incorrect."})

        # read the file content, if it is not read when the request is multi part then the client get an error
        fileContent = uploaded(fileSize)

        media = GenericImage()
        imgField = ImageField().clean(ContentFile(fileContent, name=fileName), media)
        media.hosted.save(fileName, imgField)
        media.save()

    return media

@require_POST
@login_required
def ajax_upload_image(request):
    try:
        media = upload_image(request)
    except Exception as e:
        return ajax_error({'error': e})

    return ajax_success({
        'media_id': media.id,
        'url': media.get_url()
    })
