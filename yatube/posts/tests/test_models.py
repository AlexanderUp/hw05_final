from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="user")
        cls.author = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост, текст, длиной более 15 символов",
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text="Comment text here",
        )
        cls.follow = Follow.objects.create(user=cls.user, author=cls.author)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работет __str__."""
        test_object_names = {
            ModelsTest.group: ModelsTest.group.title,
            ModelsTest.post: ModelsTest.post.text[:15],
            ModelsTest.comment: ModelsTest.comment.text,
        }
        for instance, expected_value in test_object_names.items():
            with self.subTest(instance=instance):
                self.assertEqual(str(instance), expected_value)

    def test_model_fields_have_correct_verbose_name(self):
        """
        Проверяем, что у полей моделей корректно отображается атрибут
        <verbose_name>.
        """
        correct_verbose_names = (
            (
                ModelsTest.group,
                {
                    "title": "Название группы",
                    "slug": "Слаг группы",
                    "description": "Описание группы",
                }
            ),
            (
                ModelsTest.post,
                {
                    "text": "Текст нового поста",
                    "pub_date": "Дата публикации",
                    "author": "Автор поста",
                    "group": "Группа",
                    "image": "Картинка",
                }
            ),
            (
                ModelsTest.comment,
                {
                    "post": "Пост, к которому относится комментарий",
                    "author": "Автор комментария",
                    "text": "Текст комментария",
                    "created": "Дата публикации комментария",
                }
            ),
            (
                ModelsTest.follow,
                {
                    "user": "User-follower",
                    "author": "User-author",
                }
            ),
        )

        for instance_tuple in correct_verbose_names:
            instance, test_dict = instance_tuple
            for field_name, expected_value in test_dict.items():
                with self.subTest(instance=instance, field_name=field_name):
                    self.assertEqual(
                        instance._meta.get_field(field_name).verbose_name,
                        expected_value
                    )

    def test_model_fields_have_correct_help_text(self):
        """
        Проверяем, что у полей моделей корректно отображается атрибут
        <help_text>.
        """
        correct_help_texts = (
            (
                ModelsTest.group,
                {
                    "title": "Введите название группы",
                    "slug": "Введите слаг группы",
                    "description": "Введите описание группы",
                }
            ),
            (
                ModelsTest.post,
                {
                    "text": "Введите текст нового поста",
                    "author": "Имя автора нового поста",
                    "group": "Группа, к которой будет относиться пост",
                    "image": "Выберите картинку",
                }
            ),
            (
                ModelsTest.comment,
                {
                    "post": "Комментированный пост",
                    "author": "Автор комментария к посту",
                    "text": "Напишите комментарий",
                }
            ),
            (
                ModelsTest.follow,
                {
                    "user": "User, that follows",
                    "author": "Author followed by",
                }
            ),
        )

        for instance_tuple in correct_help_texts:
            instance, test_dict = instance_tuple
            for field_name, expected_value in test_dict.items():
                with self.subTest(instance=instance, field_name=field_name):
                    self.assertEqual(
                        instance._meta.get_field(field_name).help_text,
                        expected_value
                    )

    def test_unique_constraint(self):
        """
        Проверяем работоспособность ограничения БД по уникальности.
        """
        self.assertEqual(Follow.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(
                user=ModelsTest.user, author=ModelsTest.author
            )

    def test_self_follow_is_not_possible_constraint(self):
        """
        Проверяем, что пользователь не может подписаться сам на себя.
        """
        self.assertEqual(Follow.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(
                user=ModelsTest.user, author=ModelsTest.user
            )
