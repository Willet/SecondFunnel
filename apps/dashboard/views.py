import json
import collections
import requests
from time import sleep

from django import forms
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, render, get_object_or_404
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST

from apps.assets.models import Category, Page, Product, Store, ProductImage
from apps.dashboard.models import DashBoard, UserProfile, Query
from apps.scrapy.views import scrape

LOGIN_URL = '/dashboard/login'
API_URL = '/api2/'


class ProductAddForm(forms.Form):
    selection_choices = (
        ('URL', 'URL'),
        ('SKU', 'SKU'),
        ('ID', 'ID')
    )
    selection = forms.ChoiceField(choices=selection_choices)
    num = forms.CharField(label='Number', max_length=100)
    priority = forms.CharField(label='Priority (Optional)', max_length=100)
    category = forms.CharField(label='Category (Optional)', max_length=100)


class ProductRemoveForm(forms.Form):
    selection_choices = (
        ('URL', 'URL'),
        ('SKU', 'SKU'),
        ('ID', 'ID')
    )
    selection = forms.ChoiceField(choices=selection_choices)
    num = forms.CharField(label='Number', max_length=100)


class ContentAddForm(forms.Form):
    selection_choices = (
        ('URL', 'URL'),
        ('ID', 'ID')
    )
    selection = forms.ChoiceField(choices=selection_choices)
    num = forms.CharField(label='Number', max_length=100)
    category = forms.CharField(label='Category (Optional)', max_length=100)


class ContentRemoveForm(forms.Form):
    selection_choices = (
        ('URL', 'URL'),
        ('ID', 'ID')
    )
    selection = forms.ChoiceField(choices=selection_choices)
    num = forms.CharField(label='Number', max_length=100)


def error(error_message):
    print error_message
    response = {'error': error_message}
    return HttpResponseServerError(json.dumps(response), content_type='application/json')

# @cache_page(60*60)  # cache page for an hour
# @login_required(login_url=LOGIN_URL)
# @never_cache
def get_data(request):
    """ Executes a 'query' to get analytics data from a server and return the data in JSON format.

    Takes a queries id and determines if a user is allowed to make this request. If all checks
    work out and the query exists then a JSON containing data is returned. Note that different
    query types return data in different JSON layouts.
    """
    response = {'error': 'Retrieving data failed'}
    if request.method == 'GET':

        try:  # get user data
            user = User.objects.get(pk=request.user.pk)
            profile = UserProfile.objects.get(user=user)
        except ObjectDoesNotExist:
            return error('User profile does not exist')
        request_get = request.GET

        # Get dashboard
        dashboard_id = -1
        if 'dashboard' in request_get:
            dashboard_id = request_get['dashboard']
        try:
            cur_dashboard_page = DashBoard.objects.get(pk=dashboard_id).page
        except (DashBoard.MultipleObjectsReturned, DashBoard.DoesNotExist):
            return error("Dashboard error, multiple or no dashboards found")

        # Determine if user can view dashboard
        if not profile.dashboards.all().filter(pk=dashboard_id):
            # can't view page
            return error("User: " + user.username + "cannot view dashboard: " + dashboard_id)

        # Determine if query exists and if so get query and data
        if 'query_name' in request_get:
            query_name = request_get['query_name']
            try:
                query = Query.objects.filter(identifier=query_name).select_subclasses()
                if query:
                    query = query[0]
                else:
                    return error('Query {} needs to be defined.'.format(query_name))
            except (Query.MultipleObjectsReturned, Query.DoesNotExist):
                return error('Multiple queries found, or query does not exist')
            # execute query and set response
            # success case
            response = query.get_response(cur_dashboard_page)
            return HttpResponse(response, content_type='application/json')
        else:  # query id not included in request
            return error('Query ID was not included in request')

    # last ditch. Unknown error happened which caused success case to not happen
    return HttpResponse(response, content_type='application/json')

@login_required(login_url=LOGIN_URL)
def index(request):
    """ The main page of the dashboard, shows a list of
    dashboards that the current user can view.
    """
    user = User.objects.get(pk=request.user.pk)
    context_dict = {}
    try:
        profile = UserProfile.objects.get(user=user)
        dashboards = profile.dashboards.all()
        context_dict = {'dashboards': [{'site': dashboards[x].site_name,
                                        'url_slug': dashboards[x].page.url_slug} for x in range(0, dashboards.count())]}
    except UserProfile.DoesNotExist:
        print "user does not exist"

    context = RequestContext(request)
    return render_to_response('dashboard_index.html', context_dict, context)

@login_required(login_url=LOGIN_URL)
def dashboard(request, dashboard_slug):
    """The analytics dashboard.
    The user must be able to view the dashboard.
    """
    profile = UserProfile.objects.get(user=request.user)
    dashboards = profile.dashboards.all()
    dashboard = dashboards.filter(page__url_slug=dashboard_slug).first()
    if not dashboard:
        return HttpResponseRedirect('/dashboard')
    dashboard_id = dashboard.id

    if not dashboard_id or not profile.dashboards.filter(id=dashboard_id):
        # can't view page
        return HttpResponseRedirect('/dashboard/')
    else:
        context_dict = {}
        try:
            cur_dashboard = DashBoard.objects.get(pk=dashboard_id)
        except (DashBoard.MultipleObjectsReturned, DashBoard.DoesNotExist):
            return HttpResponseRedirect('/dashboard/')
        context_dict['dashboard_id'] = cur_dashboard.pk
        context_dict['siteName'] = cur_dashboard.site_name
        context_dict['dashboard_slug'] = dashboard_slug
        return render(request, 'dashboard.html', context_dict)

@login_required(login_url=LOGIN_URL)
def overview(request):
    """A list of all active pages and clients.
    The user must be able to view the dashboard.
    """
    stores = Store.objects.prefetch_related(
        'pages',
        'pages__feed'
    )
    return render_to_response('overview.html', {
        'stores': stores,
        'domain': settings.WEBSITE_BASE_URL,
    })

@login_required(login_url=LOGIN_URL)
def dashboard_manage(request, dashboard_slug):
    productAddForm = ProductAddForm()
    productRemoveForm = ProductRemoveForm()
    contentAddForm = ContentAddForm()
    contentRemoveForm = ContentRemoveForm()

    profile = UserProfile.objects.get(user=request.user)
    dashboard = profile.dashboards.all().filter(page__url_slug=dashboard_slug)

    if not dashboard:
        return HttpResponseRedirect('/dashboard')
    dashboard_id = dashboard.first().id
    page_id = dashboard.first().page_id

    if not dashboard_id or not profile.dashboards.filter(id=dashboard_id):
        return HttpResponseRedirect('/dashboard/')
    else:
        try:
            cur_dashboard = DashBoard.objects.get(pk=dashboard_id)
        except (DashBoard.MultipleObjectsReturned, DashBoard.DoesNotExist):
            return HttpResponseRedirect('/dashboard/')
        
        context = RequestContext(request)
        cur_dashboard_page = cur_dashboard.page

        return render(request, 'manage.html', {
                'productAddForm': productAddForm,
                'productRemoveForm': productRemoveForm, 
                'contentAddForm': contentAddForm,
                'contentRemoveForm': contentRemoveForm,
                'context': context, 
                'siteName': cur_dashboard.site_name, 
                'url_slug': page_id,
                'page': cur_dashboard_page
            })

@login_required(login_url=LOGIN_URL)
def dashboard_tiles(request, dashboard_slug):
    profile = UserProfile.objects.get(user=request.user)
    dashboard = profile.dashboards.all().filter(page__url_slug=dashboard_slug)

    if not dashboard:
        return HttpResponseRedirect('/dashboard')
    dashboard_id = dashboard.first().id
    page_id = dashboard.first().page_id

    if not dashboard_id or not profile.dashboards.filter(id=dashboard_id):
        return HttpResponseRedirect('/dashboard/')
    else:
        try:
            cur_dashboard = DashBoard.objects.get(pk=dashboard_id)
        except (DashBoard.MultipleObjectsReturned, DashBoard.DoesNotExist):
            return HttpResponseRedirect('/dashboard/')

        page = Page.objects.get(pk=page_id)
        tileList = page.feed.tiles.all()

        allProducts = []
        for tile in tileList:
            tile = json.loads(tile.ir_cache)
            tile_id = tile['tile-id']
            tile_prio = tile['priority']
            if 'default-image' in tile:
                try:
                    tile_img = ProductImage.objects.get(id=tile['default-image']).url
                except ProductImage.DoesNotExist:
                    tile_img = "Does not exist"
            else:
                tile_img = tile['url']

            allProducts.append({
                'id': tile_id, 
                'img': tile_img,
                'priority': tile_prio
            })

        context = RequestContext(request)
        cur_dashboard_page = cur_dashboard.page

        return render(request, 'tiles.html', {
                'productsList': allProducts,
                'context': context, 
                'siteName': cur_dashboard.site_name, 
                'url_slug': page_id,
                'page': cur_dashboard_page
            })

def user_login(request):
    """
    Allows the user to log in to our servers.

    This does the same thing as the admin login screen, but looks nicer and will
    redirect to the dashboard.
    """
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # authenticate username/password combo, store user
        user = authenticate(username=username, password=password)

        if user is not None:  # if authentication was successful
            if user.is_active:  # could have been deactivated
                login(request, user)  # log the user in.
                return HttpResponseRedirect('/dashboard/')
            else:  # user account was deactivated
                return HttpResponse("Your SecondFunnel account is disabled")

        else:  # invalid account
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    else:  # display form. most likely http GET
        return render_to_response('login.html',
                                  {},  # no context variables to pass
                                  context)

@login_required(login_url=LOGIN_URL)
def user_logout(request):
    logout(request)
    # Take the user back to the homepage.
    return HttpResponseRedirect('/dashboard/')
