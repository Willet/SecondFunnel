"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client


class HandlerTest(TestCase):
    """Tests checking that handlers return a page (tests for 200 status)"""
    def test_pinpoint_loads(self):
        """Tests that loading a pinpoint page returns a 200 status."""
        c = Client()
        response = c.get("/pinpoint/1/")
        self.assertEqual(response.status_code, 200)

    def test_pinpoint_generic_loads(self):
        """Tests that loading a pinpoint page returns a 200 status."""
        c = Client()
        response = c.get("/pinpoint/generic/1/")
        self.assertEqual(response.status_code, 200)

