from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.forms import ImageField, ValidationError

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


def modify_campaign(request, live):
    """
    Sets a campaign's accessability given by the the request.

    @deprecated: Pinpoint pages are now always live.

    @param request: The request containing the campaign id.
    @param live: Whether the page should be live or not.

    @return: An HttpsResponse containing json with a success attribute.
    """
    if not request.method == 'POST':
        return ajax_error()

    campaign_id = request.POST.get('campaign_id')
    if not campaign_id:
        return ajax_error()

    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return ajax_error()
    else:
        if not request.user in campaign.store.staff.all():
            return ajax_error()

        campaign.live = live
        campaign.save()

    return ajax_success()


@login_required
def upload_image(request):
    """
    Uploads an image given by the request.

    @param request: The request containing the image.

    @return: An HttpResponse object containing json.
    """
    # this should only be called by post request
    if not request.method == 'POST':
        return ajax_error()
    # in IE this gets sent as a file
    if 'qqfile' in request.FILES:
        try:
            media = GenericImage()
            imgField = ImageField().clean(request.FILES['qqfile'], media)
            media.hosted.save(imgField.name, imgField)
            media.save()
        except KeyError:
            return ajax_error()
        except ValidationError:
            return ajax_error()

    # in other browsers we read this using request.read
    else:
        # read file info from stream
        uploaded = request.read

        try:
            # get file size
            fileSize = int(uploaded.im_self.META.get("CONTENT_LENGTH", None))
        except TypeError:
            return ajax_error()

        # get file name
        fileName = request.GET.get('qqfile', None)

        if None in (fileSize, fileName):
            return ajax_error()

        # read the file content, if it is not read when the request is multi part then the client get an error
        fileContent = uploaded(fileSize)

        try:
            media = GenericImage()
            imgField = ImageField().clean(ContentFile(fileContent, name=fileName), media)
            media.hosted.save(fileName, imgField)
            media.save()
        except ValidationError:
            return ajax_error()

    return ajax_success({
        'media_id': media.id,
        'url': media.get_url()
    })
