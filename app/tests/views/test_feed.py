from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Inkling, Memo, Query, Reference, Tag


class BaseFeedViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user(username='testuser', password='testpass')

    def view_url_accessible_by_name(self, url_name, args):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse(url_name, args=args))
        self.assertEqual(response.status_code, 200)


class TagFeedViewTest(BaseFeedViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Tag.objects.create(user=cls.test_user, name="TestTag")

    def test_tag_feed_view(self):
        self.view_url_accessible_by_name('view_tag', [Tag.objects.first().pk]) # type: ignore


class SearchFeedViewTest(BaseFeedViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_tag_feed_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('search'), data=dict(query='test'))
        self.assertEqual(response.status_code, 200)


class MemoFeedViewTest(BaseFeedViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Memo.objects.create(user=cls.test_user, title="TestTitle", content="TestContent")

    def test_tag_feed_view(self):
        self.view_url_accessible_by_name('view_memo', [Memo.objects.first().pk]) # type: ignore


class InklingFeedViewTest(BaseFeedViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Inkling.objects.create(user=cls.test_user, title="TestTitle", content="TestContent")

    def test_tag_feed_view(self):
        self.view_url_accessible_by_name('view_inkling', [Inkling.objects.first().pk]) # type: ignore


