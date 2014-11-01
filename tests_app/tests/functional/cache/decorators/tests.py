# -*- coding: utf-8 -*-
import uuid

from django.test import TestCase
from django.utils.encoding import force_text
from django.contrib.auth import get_user_model
Users = get_user_model()

from .urls import urlpatterns


class _TestCacheAbstract(TestCase):
    urls = urlpatterns


class TestCacheResponseFunctionally(_TestCacheAbstract):

    def test_should_return_response(self):
        resp = self.client.get('/hello/')
        self.assertEqual(force_text(resp.content), '"Hello world"')

    def test_should_return_same_response_if_cached(self):
        resp_1 = self.client.get('/hello/')
        resp_2 = self.client.get('/hello/')
        self.assertEqual(resp_1.content, resp_2.content)

    def test_cache_key_should_differ_with_query_param(self):
        """ query twice, each query param should return a unique message
        """
        resp = self.client.get('/hello-param/?param=world')
        self.assertEqual(force_text(resp.content), '"Hello world"')

        resp = self.client.get('/hello-param/?param=everyone')
        self.assertEqual(force_text(resp.content), '"Hello everyone"')


class TestCacheUserFunctionally(_TestCacheAbstract):
    url = '/hello-user/'

    @staticmethod
    def _create_user():
        user_pass = str(uuid.uuid4())
        return Users.objects.create_user(
            username=user_pass, password=user_pass)

    def _login_user(self, user):
        """ when the user is created, the username is the same as the password
        """
        login_success = self.client.login(
            username=user.username, password=user.username)
        self.assertTrue(login_success)

    def test_cache_authentication(self):
        """ the view only allows authenticated requests
        """
        # resp = self.client.get(self.url)
        # self.assertEqual(resp.status_code, 403)

        # create a user, login, get custom hello message, logout
        user1 = self._create_user()
        self._login_user(user1)
        resp1 = self.client.get(self.url)
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(
            force_text(resp1.content), '"Hello {}"'.format(user1.username))

        # logout, 403 is returned
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

        # create new user, get a new hello message
        user2 = self._create_user()
        self._login_user(user2)
        resp2 = self.client.get(self.url)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(
            force_text(resp2.content), '"Hello {}"'.format(user2.username))

        # content from both responses must be different, since usernames differ
        self.assertNotEqual(
            force_text(resp1.content), force_text(resp2.content))
