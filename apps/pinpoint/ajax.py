from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.forms import ImageField, ValidationError

from apps.assets.models import GenericImage
from apps.pinpoint.models import Campaign
from apps.utils.ajax import ajax_success, ajax_error


@login_required
def campaign_save_draft(request):
    return modify_campaign(request, False)


@login_required
def campaign_publish(request):
    return modify_campaign(request, True)


def modify_campaign(request, live):
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


def upload_image(request):
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
            return ajax_error()

        # read the file content, if it is not read when the request is multi part then the client get an error
        fileContent = uploaded(fileSize)

        media = GenericImage()
        imgField = ImageField().clean(ContentFile(fileContent, name=fileName), media)
        media.hosted.save(fileName, imgField)
        media.save()

    return media

@login_required
def ajax_upload_image(request):
    if not request.method == 'POST':
        return ajax_error()

    try:
        media = upload_image(request)
    except:
        return ajax_error()

    return ajax_success({
        'media_id': media.id,
        'url': media.get_url()
    })
