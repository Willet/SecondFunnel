from django.conf.urls import patterns, url

urlpatterns = patterns('apps.ads.views',
    url(r'^(?P<page_id>\d+)/?$', 'campaign', name='ad_unit'),
    url(r'^(?P<template_slug>[^/]+)/(?P<ad_slug>[^/]+)/?$', 'demo_page_by_slug'),
)
