from functools import partial
import json
import os
import re
import urllib2
from urlparse import urlunparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile, File
from django.contrib.auth.views import login
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Template, Context, loader
from django.http import HttpResponse, HttpResponseServerError
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify, safe
from django.utils.encoding import force_unicode
from django.views.decorators.cache import cache_page
from social_auth.db.django_models import UserSocialAuth
from storages.backends.s3boto import S3BotoStorage

from apps.analytics.models import Category
from apps.assets.models import ExternalContent, ExternalContentType, \
    Product, Store
from apps.intentrank.views import get_seeds
from apps.pinpoint.models import Campaign, BlockType
from apps.pinpoint.decorators import belongs_to_store
import apps.pinpoint.wizards as wizards
from apps.utils import noop
import apps.utils.base62 as base62
from apps.utils.social.instagram_adapter import Instagram
from apps.utils.image_service.api import queue_processing

@login_required
def login_redirect(request):
    """
    Redirects user to store admin page if they are only staff for one store.

    @param request: The request for this page.

    @return: An HttpResponseRedirect that redirects the user to either a store admin
    page, or a page where the user can pick which store they want to view.
    """
    store_set = request.user.store_set
    if store_set.count() == 1:
        return redirect('store-admin', store_id=str(store_set.all()[0].id))
    else:
        return redirect('admin')


def login_success_redirect(request):
    """Redirects user to store admin page if he/she already logged in
    and attempts to log in again.
    """
    if request.user.is_authenticated():
        return login_redirect(request)
    else:
        return login(request)


@login_required
def social_auth(request):
    """
    Redirect after some social action (account association, probably).

    @param request: The request for this page.

    @return: An HttpResponse that redirects the user to the asset_manager
    page, or a page where the user can pick which store they want to view
    """
    store_set = request.user.store_set
    if store_set.count() == 1:
        return redirect('asset-manager', store_id=str(store_set.all()[0].id))
    else:
        return redirect('admin')


@login_required
def admin(request):
    """
    Allows the user to select which store they want to view.

    @param request: The request for this page.

    @return: An HttpResponse which renders the page template.
    """
    return render_to_response('pinpoint/admin_staff.html', {
        "stores": request.user.store_set
    }, context_instance=RequestContext(request))


@belongs_to_store
@login_required
def store_admin(request, store_id):
    """
    Displays the pinpoint pages for the given store. User can make new pages,
    edit pages, and get links to pages.

    @param request: The request for this page.
    @param store_id: The id of the store to show pinpoint pages for.

    @return: An HttpResponse which renders the page template.
    """
    store = get_object_or_404(Store, pk=store_id)

    return render_to_response('pinpoint/admin_store.html', {
        "store": store
    }, context_instance=RequestContext(request))


@login_required
def new_campaign(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    return render_to_response('pinpoint/admin_new_campaign.html', {
        "store": store,
        "block_types": BlockType.objects.all(),
    }, context_instance=RequestContext(request))


@login_required
def edit_campaign(request, store_id, campaign_id):
    store = get_object_or_404(Store, pk=store_id)
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    block_type = campaign_instance.content_blocks.all()[0].block_type

    return getattr(wizards, block_type.handler)(
        request, store, block_type, campaign=campaign_instance)

@login_required
def delete_campaign(request, store_id, campaign_id):
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)
    campaign_instance.live = False
    campaign_instance.save()

    messages.success(request, "Your page was deleted.")

    return redirect('store-admin', store_id=store_id)


@login_required
def block_type_router(request, store_id, block_type_id):
    """Resolves the handler that renders a "block type".

    Handler information is stored in the database.
    """
    store = get_object_or_404(Store, pk=store_id)
    block_type = get_object_or_404(BlockType, pk=block_type_id)

    return getattr(wizards, block_type.handler)(request, store, block_type)


@login_required
def store_analytics_admin(request, store_id):
    store = get_object_or_404(Store, pk=store_id)

    return analytics_admin(request, store)


@login_required
def campaign_analytics_admin(request, store_id, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)

    return analytics_admin(
        request, campaign.store, campaign=campaign, is_overview=False)


@belongs_to_store
@login_required
def analytics_admin(request, store, campaign=False, is_overview=True):
    categories = Category.objects.filter(enabled=True)
    store_type = ContentType.objects.get_for_model(Store)
    campaign_type = ContentType.objects.get_for_model(Campaign)

    return render_to_response('pinpoint/admin_analytics.html', {
        'is_overview': is_overview,
        'store': store,
        'campaign': campaign,
        'categories': categories
    }, context_instance=RequestContext(request))


@belongs_to_store
@login_required
def asset_manager(request, store_id):
    """renders the page that allows store owners to tag their instagram photos
    on their products (or, logically, the other way around).
    """
    store = get_object_or_404(Store, pk=store_id)
    user = request.user

    # Check if connected to Instagram... for now
    try:
        instagram_user = store.social_auth.get(provider='instagram')
    except UserSocialAuth.DoesNotExist:
        instagram_user = None

    if not instagram_user:
        try:
            instagram_user = user.social_auth.get(provider='instagram')
        except UserSocialAuth.DoesNotExist:
            instagram_user = None

    if instagram_user:
        instagram_connector = Instagram(tokens=instagram_user.tokens)
        contents = instagram_connector.get_content(count=500)

        for instagram_obj in contents:
            content_type = ExternalContentType.objects.get(
                slug=instagram_obj.get('type'))

            new_content, created = ExternalContent.objects.get_or_create(
                store=store,
                original_id=instagram_obj.get('original_id'),
                content_type=content_type)

            if created:
                new_content.text_content = instagram_obj.get('text_content')

                new_content.image_url = queue_processing(
                    instagram_obj.get('image_url'),
                    store_slug=store.slug,
                    image_type=instagram_obj.get('type')
                )
                new_content.save()

    all_contents = store.external_content.all()

    return render_to_response('pinpoint/asset_manager.html', {
        "store": store,
        "instagram_user": instagram_user,
        "content": [
            ("Needs Review", "needs_review",
                all_contents.filter(approved=False, active=True)),
            ("Rejected", "rejected",
                all_contents.filter(active=False)),
            ("Approved", "approved",
                all_contents.filter(approved=True, active=True))
        ],
        "store_id": store_id
    }, context_instance=RequestContext(request))


# origin: campaigns with short URLs are cached for 30 minutes
@cache_page(60 * 30)
def campaign_short(request, campaign_id_short):
    """base62() is a custom function, so to figure out the long
    campaign URL, go to http://elenzil.com/esoterica/baseConversion.html
    and decode with the base in utils/base62.py.

    The long URL is (currently) /pinpoint/(long ID).
    """
    return campaign(request, base62.decode(campaign_id_short))


def campaign(request, campaign_id):
    campaign_instance = get_object_or_404(Campaign, pk=campaign_id)

    arguments = {
        "campaign": campaign_instance,
        "columns": range(4),
        "preview": not campaign_instance.live
    }
    context = RequestContext(request)

    if hasattr(campaign_instance.store, "theme"):
        context.update(arguments)
        return campaign_to_theme_to_response(campaign_instance, arguments,
                                             context, request=request)
    else:
        return render_to_response('pinpoint/campaign.html', arguments,
                                  context_instance=context)


def generate_static_campaign(campaign, contents, force=False):
    """write a PinPoint page to local storage.

    returns whether the file was written.
    """
    write = False
    filename = '%s/static/pinpoint/html/%s.html' % (os.path.dirname(
        os.path.realpath(__file__)), campaign.id)
    # the "robust" file exists method: stackoverflow.com/a/85237
    if force:
        write = True
    else:
        try:
            with file(filename) as tf:
                pass
        except IOError:
            write = True

    if write:
        try:
            import codecs
            tf2 = codecs.open(filename, "wb", "UTF-8")
            tf2.write(unicode(contents))
            tf2.close()
        except IOError:
            pass

    return filename, write


def save_static_campaign(campaign, local_filename, request=None):
    """Uploads the html string (contents) to s3 under the folder (campaign).

    Also _attempts_ to save its known static dependencies in the same s3
    bucket, but ONLY if request is supplied (required).

    Dependency resolution only goes so far - it will NOT search for
    dependencies within dependencies.
    """
    filename = '%s/index.html' % campaign.id  # does not expire.

    try:
        storage = S3BotoStorage(bucket=settings.STATIC_CAMPAIGNS_BUCKET_NAME,
                                access_key=settings.AWS_ACCESS_KEY_ID,
                                secret_key=settings.AWS_SECRET_ACCESS_KEY,)
        import codecs
        # local_file = file(local_filename)
        try:
            open_encoding = int(request.GET.get('open_encoding', '0'))
            if open_encoding == 0:
                local_file = codecs.open(local_filename, encoding='utf-8')
            elif open_encoding == 1:
                local_file = codecs.open(local_filename, encoding='utf-32')
            elif open_encoding == 2:
                local_file = file(local_filename, 'r')
        except ValueError:  # not int
            local_file = file(local_filename, request.GET.get('open_encoding'))

        contents = local_file.read()
        local_file.seek(0)
        if isinstance(contents, unicode):
            contents = contents.encode('utf-8')

        django_file = File(local_file)
        django_file.content_type = 'text/html'

        try:
            save_mode = int(request.GET.get('save_mode', '7'))
            if save_mode == 0:
                storage.save(filename, django_file)
            elif save_mode == 1:
                storage.save(filename, django_file.read())
            elif save_mode == 2:
                storage.save(filename, django_file.read().encode('utf-8'))
            elif save_mode == 3:
                storage.save(filename, django_file.read().decode('utf-8'))
            elif save_mode == 4:
                storage.save(filename, django_file.read().encode('utf-32'))
            elif save_mode == 5:
                storage.save(filename, django_file.read().decode('utf-32'))
            elif save_mode == 6:
                storage.save(filename, contents)
            elif save_mode == 7:
                storage.save(filename, local_file)
        except ValueError:  # not int
            storage.save(filename, request.GET.get('cust_val'))
        except UnicodeDecodeError:  # some crap happened with 2~5
            storage.save(filename, django_file.read().encode(
                request.GET.get('cust_encoding')))

    except IOError, err:
        # storage is not available. bring attention if it was forced
        if settings.DEBUG or request.GET.get('debug', '0') == '1':
            raise IOError(err)
        else:
            return None  # this means "don't deal with the dependencies"

    # save dependencies
    dependencies = re.findall('/static/[^ \'\"]+\.(?:css|js|jpe?g|png|gif)',
                              contents)
    try:
        for dependency in dependencies:
            dependency_abs_url = urlunparse(('http', request.META['HTTP_HOST'],
                                             dependency, None, None, None))
            try:
                dependency_contents = urllib2.urlopen(dependency_abs_url).read()
            except IOError:  # 404
                continue  # I am not helpful; going to work on something else

            # this can be binary
            yet_another_file = ContentFile(dependency_contents)
            storage.save(dependency, yet_another_file)
    except (IOError, AttributeError), err:
        # AttributeError is for accessing empty requests
        if settings.DEBUG:
            raise IOError(err)
        else:
            return None


def campaign_to_theme_to_response(campaign, arguments, context=None,
                                  request=None):
    """Generates the HTML page for a standard pinpoint product page.

    Related products are populated statically only if a request object
    is provided.
    """
    if not context:
        context = Context()
    context.update(arguments)

    related_results = []

    # TODO: Content blocks don't make as much sense now; when to clean up?
    # TODO: If we keep content blocks, should this be a method?
    # Assume only one content block
    content_block = campaign.content_blocks.all()[0]

    product = content_block.data.product
    product.json = json.dumps(product.data(raw=True))

    campaign.stl_image = getattr(content_block.data, 'get_ls_image', noop)(url=True) or ''
    campaign.featured_image = getattr(content_block.data, 'get_image', noop)(url=True) or ''
    campaign.description = safe(content_block.data.description or product.description)
    campaign.template = slugify(content_block.block_type.name)

    if request:
        # "borrow" IR for results
        related_results = get_seeds(request, store=campaign.store.slug,
                                    campaign=campaign.id,
                                    seeds=product.id,
                                    results=100,
                                    raw=True)
    context.update({
        'product': product,
        'campaign': campaign,
        'backup_results': related_results,
    })

    theme = campaign.store.theme
    page_str = theme.page

    actions = {
        'template': loader.get_template,
        'theme': partial(getattr, theme)
    }

    # Replace necessary tags
    for field, details in theme.REQUIRED_FIELDS.iteritems():
        type = details.get('type')
        values = details.get('values')

        sub_values = []
        for value in values:
            result = actions.get(type, noop)(value)

            # TODO: Do we need to render, or can we just convert to string?
            if isinstance(result, Template):
                result = result.render(context)
            else:
                result = result.encode('unicode-escape')

            sub_values.append(result)

        regex = r'\{\{\s*' + field + '\s*\}\}'
        page_str= re.sub(regex, ''.join(sub_values), page_str)

    # Page content
    page = Template(page_str)

    # Render response
    rendered_page = page.render(context)
    if isinstance(rendered_page, unicode):
        rendered_page = rendered_page.encode('utf-8')
    rendered_page = unicode(rendered_page, 'utf-8')

    (name, written) = generate_static_campaign(campaign, rendered_page,
        force=settings.DEBUG or request.GET.get('regen', '0') == '1')
    if written or settings.DEBUG or request.GET.get('regen', '0') == '1':
        save_static_campaign(campaign, name, request=request)

    return HttpResponse(rendered_page)


def app_exception_handler(request):
    """Renders the "something broke" page. JS console shows the error."""
    import sys, traceback

    type, exception, tb = sys.exc_info()
    stack = traceback.format_exc().splitlines()

    return HttpResponseServerError(loader.get_template('500.html').render(
        Context({'exception': exception,
                 'traceback': '\n'.join(stack)})))