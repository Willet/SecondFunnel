from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.forms import ImageField, ValidationError
from django.views.decorators.http import require_POST

from apps.assets.models import GenericImage
from apps.utils.ajax import ajax_success, ajax_error


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
            return ajax_error()

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
    except:
        return ajax_error()

    return ajax_success({
        'media_id': media.id,
        'url': media.get_url()
    })
