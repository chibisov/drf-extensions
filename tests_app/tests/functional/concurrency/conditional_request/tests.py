from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Book
from django.test import override_settings


@override_settings(ROOT_URLCONF='tests_app.tests.functional.concurrency.conditional_request.urls')
class BookAPITestCases(APITestCase):
    """
    Run the conditional requests test cases (django 1.10 only):

        `tox -e django.1.10 -- tests_app.tests.functional.concurrency.conditional_request.tests`
    """
    def setUp(self):
        # create a book
        self.book = Book.objects.create(name='The Summons',
                                        author='Stephen King',
                                        issn='9780345531988')

    def alter_book_issn(self, issn='0123456789012'):
        """Mimic alteration of object in the DB."""
        self.book.issn = issn
        self.book.save()
        return self.book

    def test_book_retrieve_cache_hit(self):
        """Test idempotent retrieve using 'If-None-Match' HTTP header, should result in HTTP 304."""
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json')
        self.assertEqual(book_response.status_code, status.HTTP_200_OK)
        # memorize the ETag from the response to send with the next request
        etag = book_response['ETag']

        # issue the same request again
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json',
                                        HTTP_IF_NONE_MATCH=etag)

        self.assertEqual(book_response.status_code, status.HTTP_304_NOT_MODIFIED,
                         'The response status code must be 304!')
        self.assertEqual(book_response['ETag'], etag)

    def test_book_retrieve_cache_miss(self):
        """Test idempotent retrieve using 'If-None-Match' HTTP header, should result in HTTP 200."""
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json')
        self.assertEqual(book_response.status_code, status.HTTP_200_OK)
        # memorize the ETag from the response to send with the next request
        etag = book_response['ETag']

        # simulate background activity on the book
        self.alter_book_issn()

        # issue the same request again
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json',
                                        HTTP_IF_NONE_MATCH=etag)

        self.assertEqual(book_response.status_code, status.HTTP_200_OK,
                         'The response status code must be 200!')
        self.assertNotEqual(book_response['ETag'], etag)

    def test_book_update(self):
        """Test an update without providing the 'ETag' HTTP header, should yield HTTP 200."""
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json')
        self.assertEqual(book_response.status_code, status.HTTP_200_OK)
        book_json = book_response.json()
        # alter the author
        book_json['author'] = 'John Grisham'
        url = reverse('book-detail', kwargs={'pk': book_json['id']})
        response = self.client.put(url,
                                   data=book_json)
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'The response status code must be 200!')
        updated_book_json = response.json()
        # print(response.json())
        self.assertEqual(updated_book_json['author'], book_json['author'], 'Author must be John Grisham!')

    def test_book_delete(self):
        """Test delete, should result in HTTP 204."""
        # retrieve
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json')
        self.assertEqual(book_response.status_code, status.HTTP_200_OK)
        # delete
        response = self.client.delete(reverse('book-detail', kwargs={'pk': self.book.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, 'The response status code must be 204!')

    def test_book_conditional_update(self):
        """Test a conditional update of a book using 'If-Match' HTTP header, should yield HTTP 200."""
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json')
        self.assertEqual(book_response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(book_response['ETag'])
        book_json = book_response.json()
        # memorize the ETag from the response to send with the next request
        etag = book_response['ETag']

        # alter the author
        book_json['author'] = 'John Grisham'
        url = reverse('book-detail', kwargs={'pk': book_json['id']})
        response = self.client.put(url,
                                   data=book_json,
                                   HTTP_IF_MATCH=etag)  # <-- set the ETag header to trigger the conditional request

        # ######################## ######################## ########################
        # this update must succeed, since the if-match header is the same as the ETag sent from the server!
        self.assertNotEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED, 'The response status code must '
                                                                                       'not be 412!')
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'The response status code must be 200!')
        # ######################## ######################## ########################

        updated_book_json = response.json()
        # print(response.json())
        self.assertEqual(updated_book_json['author'], book_json['author'], 'Author must be John Grisham!')

    def test_book_conditional_update_fail(self):
        """Test a conditional update of a book using 'If-Match' HTTP header, should yield HTTP 200."""
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json')
        self.assertEqual(book_response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(book_response['ETag'])
        book_json = book_response.json()
        # memorize the ETag from the response to send with the next request
        etag = book_response['ETag']

        # mimic background activity
        self.alter_book_issn()

        # alter the author
        book_json['author'] = 'John Grisham'
        url = reverse('book-detail', kwargs={'pk': book_json['id']})
        response = self.client.put(url,
                                   data=book_json,
                                   HTTP_IF_MATCH=etag)  # <-- set the ETag header to trigger the conditional request

        # ######################## ######################## ########################
        # this update must succeed, since the if-match header is the same as the ETag sent from the server!
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED, 'The response status code must '
                                                                                    'be 412!')
        # ######################## ######################## ########################

    def test_book_conditional_delete(self):
        """Test conditional delete using 'If-Match' HTTP header, should result in HTTP 204."""
        book_response = self.client.get(reverse('book-detail', kwargs={'pk': self.book.id}),
                                        CONTENT_TYPE='application/json')
        self.assertEqual(book_response.status_code, status.HTTP_200_OK)
        # memorize the ETag from the response to send with the next request
        etag = book_response['ETag']

        # delete the instance
        book_response = self.client.delete(reverse('book-detail', kwargs={'pk': self.book.id}),
                                           HTTP_IF_MATCH=etag)

        self.assertEqual(book_response.status_code, status.HTTP_204_NO_CONTENT, 'The response status code must be 204!')
