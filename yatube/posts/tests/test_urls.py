from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username="NoName")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group_test = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        cls.post_test = Post.objects.create(
            text='Тестовый пост контент',
            group=cls.group_test,
            author=cls.user,
        )

        cls.public = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{cls.group_test.slug}/',
            'posts/profile.html': f'/profile/{cls.user.username}/',
            'posts/post_detail.html': f'/posts/{cls.post_test.pk}/',
        }

        cls.private = {
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post_test.pk}/edit/': 'posts/create_post.html',
        }

    def test_public_pages(self):
        """Проверка доступности публичных страниц приложения posts."""
        for template, address in self.public.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_pages(self):
        """Проверка доступности страниц приложения posts
        для авторизованного пользователя.
        """
        for address, template in self.private.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_page(self):
        """Проверка 404 страницы."""
        pages_404 = '/posts/test404/'
        response = self.authorized_client.get(pages_404)
        self.assertEqual(response.status_code, 404)
