from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

LEN_POST: int = 15


class Group(models.Model):
    title = models.CharField(
        verbose_name='Группа',
        help_text='Выберите группу для поста',
        max_length=200)
    slug = models.SlugField(
        verbose_name='Слаг группы',
        unique=True)
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание группы'
    )

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите группу'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )


class Comment(models.Model):
    text = models.TextField('Текст', help_text='Текст нового комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comments',
        verbose_name='Ссылка на пост'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Комментарий'
    )
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    def __str__(self):
        return self.text[:LEN_POST]

    class Meta:
        ordering = ['created']
        verbose_name = "Комментарий"
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Подписчик автора'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
        help_text='Автор публикаций'
    )

    class Meta:
        db_table = 'Follow'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow')
        ]
        verbose_name_plural = 'Подписки'
