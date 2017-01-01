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

    def test_book_update(self):
        """Test an update without providing the ETag HTTP header, should yield HTTP 200."""
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

    def test_book_conditional_update(self):
        """Test conditional update of a book using 'If-Match' HTTP header, should yield HTTP 200."""
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
