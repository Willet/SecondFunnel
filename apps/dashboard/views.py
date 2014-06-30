import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page, never_cache
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template import RequestContext

from django.utils.timezone import now
from datetime import timedelta

from django.contrib.auth.models import User
from apps.dashboard.models import DashBoard, UserProfile, Query

LOGIN_URL = '/dashboard/login'


# @cache_page(60*60)  # cache page for an hour
# @login_required(login_url=LOGIN_URL)
# @never_cache
def get_data(request):
    response = {'error': 'Retrieving data failed'}
    if request.method == 'GET':
        try:
            user = User.objects.get(pk=request.user.pk)
            profile = UserProfile.objects.get(user=user)
        except ObjectDoesNotExist:
            print 'user profile does not exist'
            response['error'] = 'user profile DNE'
            response = json.dumps(response)
            return HttpResponse(response, content_type='application/json')
        request_get = request.GET

        dashboard_id = -1
        if 'dashboard' in request_get:
            dashboard_id = request_get['dashboard']
        try:
            cur_dashboard = DashBoard.objects.get(pk=dashboard_id)
        except DashBoard.MultipleObjectsReturned, DashBoard.DoesNotExist:
            print "Dashboard error, multiple or none"
            response['error'] = 'error retrieving dashboard'
            response = json.dumps(response)
            return HttpResponse(response, content_type='application/json')

        if not profile.dashboards.all().filter(pk=dashboard_id):
            # can't view page
            print "User: " + user.username + "cannot view dashboard: " + dashboard_id
            response['error'] = 'user cannot view dashboard'
            response = json.dumps(response)
            return HttpResponse(response, content_type='application/json')
        if ('query_name' in request_get) and ('campaign' in request_get):
            query_name = request_get['query_name']
            try:
                query = Query.objects.filter(identifier=query_name).select_subclasses()
                if query:
                    query = query[0]
                else:
                    print 'query {} needs to be defined.'.format(query_name)
                    response['error'] = 'query {} needs to be defined.'.format(query_name)
                    response = json.dumps(response)
                    return HttpResponse(response, content_type='application/json')
            except Query.MultipleObjectsReturned, Query.DoesNotExist:
                print 'error, multiple queries or query does not exist'
                response['error'] = 'error retrieving query'
                response = json.dumps(response)
                return HttpResponse(response, content_type='application/json')
            # set response
            response = query.get_response(cur_dashboard.page)
        else:
            response = json.dumps(response)
    return HttpResponse(response, content_type='application/json')


@login_required(login_url=LOGIN_URL)
def index(request):
    user = User.objects.get(pk=request.user.pk)
    context_dict = {}
    try:
        profile = UserProfile.objects.get(user=user)
        dashboards = profile.dashboards.all()
        context_dict = {'dashboards': [{'site': dashboard.site_name,
                                        'pk': dashboard.pk} for dashboard in dashboards]}
    except UserProfile.DoesNotExist:
        print "user does not exist"

    context = RequestContext(request)
    return render_to_response('index.html', context_dict, context)


@login_required(login_url=LOGIN_URL)
def dashboard(request, dashboard_id):
    profile = UserProfile.objects.get(user=request.user)
    if not profile.dashboards.all().filter(pk=dashboard_id):
        # can't view page
        return HttpResponseRedirect('/dashboard/')
    else:
        context_dict = {}
        try:
            cur_dashboard = DashBoard.objects.get(pk=dashboard_id)
        except DashBoard.MultipleObjectsReturned or DashBoard.DoesNotExist:
            return HttpResponseRedirect('/dashboard/')
        context_dict['dashboard_id'] = cur_dashboard.pk
        context_dict['siteName'] = cur_dashboard.site_name

        return render(request, 'dashboard.html', context_dict)


def user_login(request):
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
