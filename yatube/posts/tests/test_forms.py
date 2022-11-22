import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class CommentCreateExistTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post_test = Post.objects.create(
            text='Тестовый пост контент',
            author=cls.user,
        )
        cls.comment_test = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post_test,
            author=cls.user,
        )

    def test_authorized_comment_add(self):
        """Проверка, что авторизованный пользователь может добавлять
        комментарий"""
        comments_count = Comment.objects.count()
        post_id = self.post_test.pk
        form_data = {
            'text': 'Тестовый комментарий 2'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_guest_comment_add(self):
        """Проверка что гостевой пользователь не может добавить
        комментарий."""
        comments_count = Comment.objects.count()
        post_id = self.post_test.pk
        form_data = {
            'text': 'Тестовый комментарий 2'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        redirect = "%s?next=%s" % (
            reverse('users:login'),
            reverse('posts:add_comment', kwargs={'post_id': post_id})
        )
        self.assertRedirects(response, redirect)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateExistTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group_test = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif",
        )
        cls.post_test = Post.objects.create(
            text='Тестовый пост контент',
            group=cls.group_test,
            author=cls.user,
            image=uploaded
        )

    def test_create_post(self):
        '''Проверка создания поста в БД'''
        username = self.user.username
        posts_count = Post.objects.count()
        form_data = {
            "group": self.group_test.pk,
            "text": "Тестовый текст",
            "image": self.post_test.image
        }
        response = self.authorized_client.post(reverse("posts:create_post"),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(group=self.group_test.pk,
                                            text="Тестовый текст").exists())
        self.assertEqual(form_data['image'], "posts/small.gif")

    def test_form_edit(self):
        """Проверка редактирование поста."""
        post_id = self.post_test.pk
        username = self.user.username
        form_fields = {
            'text': 'Тестовый пост контент редактирования',
            'group': self.group_test.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_fields,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post_id}
        ))
        post = Post.objects.get(pk=post_id)
        self.assertEqual(post.text, form_fields['text'])
        self.assertEqual(post.author.username, username)
        self.assertEqual(post.group, self.group_test)
