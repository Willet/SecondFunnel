from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.light.views',
    url(r'^(?P<page_slug>\w+)/?$', 'landing_page'),
    url(r'^(?P<page_id>\d+)/?$', 'ad_banner'),
    url(r'^(?P<template_slug>[^/]+)/(?P<ad_slug>[^/]+)/?$', 'demo_page_by_slug'),
)
