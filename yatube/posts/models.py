from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название группы",
        help_text="Введите название группы",
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Слаг группы",
        help_text="Введите слаг группы",
    )
    description = models.TextField(
        verbose_name="Описание группы",
        help_text="Введите описание группы",
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст нового поста",
        help_text="Введите текст нового поста",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор поста",
        help_text="Имя автора нового поста",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
    )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="posts/",
        blank=True,
        null=True,
        help_text="Выберите картинку",
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Пост, к которому относится комментарий",
        help_text="Комментированный пост",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария",
        help_text="Автор комментария к посту",
    )
    text = models.TextField(
        verbose_name="Текст комментария",
        help_text="Напишите комментарий",
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации комментария",
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    """
    user - объект пользователя, который подписывается;
    author - объект пользователя, на которого подписываются.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="User-follower",
        help_text="User, that follows",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="User-author",
        help_text="Author followed by",
    )

    class Meta:
        verbose_name = "Follow"
        verbose_name_plural = "Follows"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_pair_user_author"
            ),
            models.CheckConstraint(
                check=~Q(user=F("author")), name="user_can_not_follow_himself"
            ),
        ]

    def __str__(self):
        return f"<{self.user}:{self.author}>"
