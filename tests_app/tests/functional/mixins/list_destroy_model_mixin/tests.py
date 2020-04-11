from django.test import override_settings

from rest_framework.test import APITestCase
from rest_framework_extensions.settings import extensions_api_settings
from rest_framework_extensions import utils

from .models import CommentForListDestroyModelMixin as Comment
from tests_app.testutils import override_extensions_api_settings


@override_settings(ROOT_URLCONF='tests_app.tests.functional.mixins.list_destroy_model_mixin.urls')
class ListDestroyModelMixinTest(APITestCase):

    def setUp(self):
        self.comments = [
            Comment.objects.create(
                id=1,
                email='example@ya.ru'
            ),
            Comment.objects.create(
                id=2,
                email='example@gmail.com'
            )
        ]
        self.protection_headers = {
            utils.prepare_header_name(extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME): 'true'
        }

    def test_simple_response(self):
        resp = self.client.get('/comments/')
        expected = [
            {
                'id': 1,
                'email': 'example@ya.ru'
            },
            {
                'id': 2,
                'email': 'example@gmail.com'
            }
        ]
        self.assertEqual(resp.data, expected)

    def test_filter_works(self):
        resp = self.client.get('/comments/?id=1')
        expected = [
            {
                'id': 1,
                'email': 'example@ya.ru'
            }
        ]
        self.assertEqual(resp.data, expected)

    def test_destroy_instance(self):
        resp = self.client.delete('/comments/1/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(1 in Comment.objects.values_list('pk', flat=True))

    def test_bulk_destroy__without_protection_header(self):
        resp = self.client.delete('/comments/')
        self.assertEqual(resp.status_code, 400)
        expected_message = {
            'detail': 'Header \'{0}\' should be provided for bulk operation.'.format(
                extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME
            )
        }
        self.assertEqual(resp.data, expected_message)

    def test_bulk_destroy__with_protection_header(self):
        resp = self.client.delete('/comments/', **self.protection_headers)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Comment.objects.count(), 0)

    @override_extensions_api_settings(DEFAULT_BULK_OPERATION_HEADER_NAME=None)
    def test_bulk_destroy__without_protection_header__and_with_turned_off_protection_header(self):
        resp = self.client.delete('/comments/')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Comment.objects.count(), 0)

    def test_bulk_destroy__should_destroy_filtered_queryset(self):
        resp = self.client.delete('/comments/?id=1', **self.protection_headers)
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.all()[0], self.comments[1])

    def test_bulk_destroy__should_not_destroy_if_client_has_no_permissions(self):
        resp = self.client.delete('/comments-with-permission/', **self.protection_headers)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(Comment.objects.count(), 2)
