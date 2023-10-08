from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Inkling, LinkType, Memo, Query, Reference, Tag


class BaseFeedViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user(username='testuser', password='testpass')

    def view_url_accessible_by_name(self, url_name, args):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse(url_name, args=args))
        self.assertEqual(response.status_code, 200)


class LinkTypeListViewTest(BaseFeedViewTest):
    def test_link_type_list_view(self):
        self.view_url_accessible_by_name('link_types', [])
