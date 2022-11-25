from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post
from ..views import POST_COUNT

User = get_user_model()
POSTS_FOR_TEST = 13


class CommentCreateExistTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')  # type: ignore
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

    def test_view_comment_in_detail_post(self):
        """Проверка, что комментарий появился на странице поста"""
        post_id = self.post_test.pk
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id}))
        first_objects = Comment.objects.filter(post_id=post_id).first()
        self.assertEqual(first_objects.text, self.comment_test.text)
        self.assertEqual(first_objects.author, self.comment_test.author)


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')  # type: ignore
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
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_gif,
            content_type="image/gif"
        )
        cls.post_test = Post.objects.create(
            text='Тестовый пост контент',
            group=cls.group_test,
            author=cls.user,
            image=cls.uploaded
        )
        cls.group_test_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test2',
            description='Описание тестовой группы 2'
        )

    def test_pages_uses_correct_template(self):
        '''Проверка использования соответствующих шаблонов.'''
        cache.clear()
        username = self.user.username
        post_id = self.post_test.pk
        slug = self.group_test.slug
        templates_pages_names = {
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:main_page'): 'posts/index.html',
            reverse('posts:post_edit', kwargs={'post_id': post_id}):
                'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': post_id}):
                'posts/post_detail.html',
            reverse('posts:group_list', kwargs={'slug': slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': username}):
                'posts/profile.html',
            'core.views.page_not_found': 'core/404.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_main_page_show_correct_context(self):
        '''Проверка context на страницах: main_page, group_list, profile.'''
        cache.clear()
        slug = self.group_test.slug
        username = self.user.username
        full_name = self.user.get_full_name()
        page_list = [
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': slug}),
            reverse('posts:profile', kwargs={'username': username})
        ]
        for page in page_list:
            response = self.authorized_client.get(page)
            first_object = response.context['page_obj'][0]
            self.assertEqual(first_object.text, self.post_test.text)
            self.assertEqual(
                first_object.author.get_full_name(), full_name)
            self.assertEqual(first_object.group.slug, slug)
            self.assertEqual(first_object.image, self.post_test.image)

    def test_post_detail(self):
        '''Проверка страницы одного поста.'''
        post_id = self.post_test.pk
        full_name = self.user.get_full_name()
        slug = self.group_test.slug
        post_text = self.post_test.text
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id}))
        first_object = response.context.get('post')
        self.assertEqual(first_object.text, post_text)
        self.assertEqual(first_object.author.get_full_name(), full_name)
        self.assertEqual(first_object.group.slug, slug)
        self.assertEqual(first_object.image, self.post_test.image)

    def test_edit_post(self):
        '''Проверка страницы редактирования поста.'''
        post_id = self.post_test.pk
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for form, expected in form_fields.items():
            with self.subTest(form=form):
                form_field = response.context.get('form').fields.get(form)
                self.assertIsInstance(form_field, expected)

    def test_create_post(self):
        '''Проверка страницы создания поста.'''
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for form, expected in form_fields.items():
            with self.subTest(form=form):
                form_field = response.context.get('form').fields.get(form)
                self.assertIsInstance(form_field, expected)

    def test_non_view_post_in_group(self):
        '''Проверка, что пост не появился в другой группе.'''
        slug = self.group_test_2.slug
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': slug}))
        count_object = len(response.context['page_obj'])
        self.assertEqual(count_object, 0)

    def test_view_post_in_main_page(self):
        '''Проверка, что пост появился на главной странице,
        странице группы и в профайле'''
        cache.clear()
        post_text = self.post_test.text
        slug = self.group_test.slug
        username = self.user.username
        page_list = [
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': slug}),
            reverse('posts:profile', kwargs={'username': username})
        ]
        for page in page_list:
            response = self.authorized_client.get(page)
            first = response.context['page_obj'][0]
            self.assertEqual(first.text, post_text)

    def test_cache_main_page(self):
        '''Проверка, что главная страница отдаёт кэшированные данные'''
        cache.clear()
        response_1 = self.authorized_client.get(reverse('posts:main_page'))
        count_1 = len(response_1.context['page_obj'])
        Post.objects.create(
            text='Тестовый текст',
            group=self.group_test,
            author=self.user
        )
        response_2 = self.authorized_client.get(reverse('posts:main_page'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:main_page'))
        count_3 = len(response_3.context['page_obj'])
        self.assertEqual(count_3, count_1 + 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Noname')  # type: ignore
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group_test = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        post_list = []
        for i in range(0, POSTS_FOR_TEST):
            new_post = Post(
                text=f'Тестовый пост контент №{i}',
                group=cls.group_test,
                author=cls.user,
            )
            post_list.append(new_post)
        Post.objects.bulk_create(post_list)

    def test_first_page(self):
        '''Проверка первой страницы паджинатора.'''
        cache.clear()
        slug = self.group_test.slug
        username = self.user.username
        page_list = [
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': slug}),
            reverse('posts:profile', kwargs={'username': username})
        ]
        for page in page_list:
            response = self.authorized_client.get(page)
            self.assertEqual(len(response.context['page_obj']), POST_COUNT)

    def test_second_page(self):
        '''Проверка второй страницы паджнатора.'''
        cache.clear()
        slug = self.group_test.slug
        username = self.user.username
        page_list = [
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': slug}),
            reverse('posts:profile', kwargs={'username': username})
        ]
        count_posts = Post.objects.count()
        count = count_posts - POST_COUNT
        if count > POST_COUNT:
            count = POST_COUNT
        for page in page_list:
            response = self.authorized_client.get(page + '?page=2')
            self.assertEqual(len(response.context['page_obj']), count)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username='User_1')
        cls.user_2 = User.objects.create(username='User_2')
        cls.user_3 = User.objects.create(username='User_3')
        cls.authorized_client_1 = Client()
        cls.authorized_client_1.force_login(cls.user_1)
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)
        cls.group_test = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        cls.post_test = Post.objects.create(
            text='Тестовый пост контент',
            group=cls.group_test,
            author=cls.user_2,
        )
        cls.test_follow = Follow.objects.create(
            user=cls.user_1,
            author=cls.user_2
        )

    def test_profile_follow(self):
        '''Проверка, что пользователь может подписаться'''
        follow_count = Follow.objects.count()
        username = self.user_3.username  # type: ignore
        self.authorized_client_1.get(reverse(
            'posts:profile_follow',
            kwargs={'username': username}
        ))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        new_follow = Follow.objects.last()
        self.assertEqual(new_follow.user, self.user_1)
        self.assertEqual(new_follow.author, self.user_3)

    def test_profile_unfollow(self):
        '''Проверка, что пользователь может отписаться'''
        follow_count = Follow.objects.count()
        username = self.user_2.username  # type: ignore
        self.authorized_client_1.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': username}
        ))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_add_post_in_follower(self):
        '''Проверка, что пост появился у тех, кто подписан'''
        Follow.objects.create(
            user=self.user_1,
            author=self.user_3
        )
        new_post = Post.objects.create(
            text='Тестовый пост контент',
            group=self.group_test,
            author=self.user_3
        )
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        first = response.context['page_obj'][0]
        self.assertEqual(new_post.text, first.text)

    def test_not_add_post_in_unfollower(self):
        '''Проверка, что пост не появился у тех, кто не подписан'''
        posts = Post.objects.filter(author=self.user_2).count()
        Post.objects.create(
            text='Тестовый пост контент',
            group=self.group_test,
            author=self.user_3
        )
        response = self.authorized_client_1.get(reverse('posts:follow_index'))
        count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts, posts)
