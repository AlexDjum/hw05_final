from django.test import Client, TestCase


class AboutURLTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_correct_page_about(self):
        templates = {
            '/about/author/': 200,
            '/about/tech/': 200,
        }

        for address, code in templates.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)
