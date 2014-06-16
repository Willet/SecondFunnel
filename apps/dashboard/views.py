import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page, never_cache
from django.contrib.auth import authenticate, login, logout

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template import RequestContext

from django.utils.timezone import now
from datetime import timedelta

from django.contrib.auth.models import User
from apps.dashboard.models import DashBoard, UserProfile, Campaign, Query

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
        except:
            print 'user profile does not exist'
            return response
        request = request.GET

        dashboard_id = -1
        if 'dashboard' in request:
            dashboard_id = request['dashboard']
        try:
            cur_dashboard = DashBoard.objects.get(pk=dashboard_id)
        except DashBoard.MultipleObjectsReturned, DashBoard.DoesNotExist:
            print "Dashboard error, multiple or none"
            return response

        if not profile.dashboards.all().filter(pk=dashboard_id):
            # can't view page
            print "User: " + user.username + "cannot view dashboard: " + dashboard_id
            return response
        if ('query_name' in request) and ('campaign' in request):
            # get data from ga based on queryName
            campaign_id = request['campaign']
            start_date = now() - timedelta(days=90)
            end_date = now()
            if not campaign_id == 'all':
                try:
                    campaign = Campaign.objects.get(identifier=campaign_id)
                except Campaign.MultipleObjectsReturned, Campaign.DoesNotExist:
                    print 'Multiple campaign or campaign dne'
                    return response
                start_date = campaign.start_date
                end_date = campaign.end_date

            query_name = request['query_name']
            try:
                query = Query.objects.filter(identifier=query_name).select_subclasses()
                print query
            except Query.MultipleObjectsReturned, Query.DoesNotExist:
                print 'error, multiple queries or query does not exist'
                return response
            query = query[0]
            # set response
            response = query.get_response(cur_dashboard.data_ids, start_date, end_date)
    print json.dumps(response)
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
        # TODO add this to model
        context_dict['campaigns'] = [{'name': 'Lived In', 'value': 'livedin'},
                                     {'name': 'Summer Loves', 'value': 'summerloves'},
                                     {'name': 'Paddington Bear', 'value': 'paddington'},
                                     {'name': 'President', 'value': 'president'}]

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
