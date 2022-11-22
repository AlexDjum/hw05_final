from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import LEN_POST, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_post_have_correct_object_names(self):
        """Проверка корректной работы __str__ в модели Post."""
        post = PostModelTest.post
        expected_object_name = post.text[:LEN_POST]
        self.assertEqual(expected_object_name, post.text)

    def test_models_group_have_correct_object_names(self):
        """Проверка корректной работы __str__ в модели Group."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name_post(self):
        """Проверка verbose_name в модели Post."""
        fields_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected in fields_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(self.post._meta.get_field(
                    field).verbose_name, expected)

    def test_verbose_name_group(self):
        """Проверка verbose_name в модели Group."""
        fields_verbose = {
            'title': 'Группа',
            'slug': 'Слаг группы',
            'description': 'Описание группы'
        }
        for field, expected in fields_verbose.items():
            with self.subTest(field=field):
                self.assertEqual(self.group._meta.get_field(
                    field).verbose_name, expected)

    def test_help_text_post(self):
        """Проверка help_text в модели Post."""
        fields_help_text = {
            'text': 'Введите текст',
            'group': 'Выберите группу'
        }
        for field, expected in fields_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(self.post._meta.get_field(
                    field).help_text, expected)

    def test_help_text_group(self):
        """Проверка help_text в модели Group."""
        fields_help_text = {
            'title': 'Выберите группу для поста',
            'description': 'Введите описание группы'
        }
        for field, expected in fields_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(self.group._meta.get_field(
                    field).help_text, expected)
