import datetime
import os
import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import ImageFieldFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostsForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="No_name_user")
        cls.group = Group.objects.create(
            title="Test_group",
            slug="Test_group_slug",
            description="Test_group_description",
        )
        cls.test_edit_post = Post.objects.create(
            text="Initial text",
            author=TestPostsForm.user,
            group=TestPostsForm.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TestPostsForm.user)

    def test_post_creation(self):
        """
        Проверяем, что после отправки формы создается новый пост с картинкой.
        """
        initial_post_count = Post.objects.count()
        self.assertEqual(initial_post_count, 1)
        self.assertEqual(TestPostsForm.user.posts.count(), initial_post_count)
        self.assertEqual(TestPostsForm.group.posts.count(), initial_post_count)

        binary_content = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00"
            b"\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )

        uploaded_image = SimpleUploadedFile(
            name="small.gif",
            content=binary_content,
            content_type="image/gif",
        )
        form_data = {
            "text": "Test text - post with image",
            "group": TestPostsForm.group.pk,
            "image": uploaded_image,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                "posts:profile", args=(TestPostsForm.user.username,)
            )
        )
        self.assertEqual(
            Post.objects.count(), (initial_post_count + 1)
        )
        self.assertEqual(
            TestPostsForm.user.posts.count(), (initial_post_count + 1)
        )
        self.assertEqual(
            TestPostsForm.group.posts.count(), (initial_post_count + 1)
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=TestPostsForm.user,
                group=form_data["group"],
                pub_date__date=datetime.date.today(),
            ).exists()
        )
        post = Post.objects.get(
            text=form_data["text"],
            author=TestPostsForm.user,
            group=form_data["group"],
            pub_date__date=datetime.date.today(),
            image="posts/small.gif",
        )
        self.assertIsInstance(post, Post)
        self.assertIsInstance(post.image, ImageFieldFile)
        self.assertTrue(os.path.exists(post.image.path))

    def test_post_edition(self):
        """
        Проверяем, что после отправки формы редактирования существующий
        пост изменяется.
        """
        initial_post_count = Post.objects.count()
        initial_author_post_count = TestPostsForm.user.posts.count()
        initial_group_post_count = TestPostsForm.group.posts.count()
        self.assertNotEqual(initial_post_count, 0)
        self.assertEqual(initial_post_count, 1)
        edit_form_data = {
            "text": "New text (edited)",
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={
                "pk": TestPostsForm.test_edit_post.pk
            }),
            data=edit_form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={
                "pk": TestPostsForm.test_edit_post.pk
            })
        )
        self.assertTrue(
            Post.objects.filter(
                text=edit_form_data["text"],
                author=TestPostsForm.user.pk,
                group=None,
                pub_date__date=datetime.date.today(),
            ).exists()
        )
        self.assertEqual(Post.objects.count(), initial_post_count)
        self.assertEqual(initial_author_post_count, initial_post_count)
        self.assertEqual(initial_group_post_count, initial_post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_creation(self):
        """
        Проверяем, что комментарий к посту создается и сохраняется в БД.
        """
        initial_post_comments_count = (
            TestPostsForm.test_edit_post.comments.count()
        )
        self.assertEqual(initial_post_comments_count, 0)
        initial_author_comments_count = (
            TestPostsForm.test_edit_post.author.comments.count()
        )
        self.assertEqual(initial_author_comments_count, 0)
        comment_form_data = {
            "text": "Comment text",
        }
        response = self.authorized_client.post(
            reverse(
                "posts:add_comment", args=(TestPostsForm.test_edit_post.pk,)
            ),
            data=comment_form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                "posts:post_detail", args=(TestPostsForm.test_edit_post.pk,)
            )
        )
        self.assertEqual(
            TestPostsForm.user.comments.count(),
            (initial_author_comments_count + 1)
        )
        self.assertEqual(
            TestPostsForm.test_edit_post.comments.count(),
            (initial_post_comments_count + 1)
        )
        self.assertTrue(
            Comment.objects.filter(text=comment_form_data["text"]).exists()
        )
        self.assertIsNotNone(
            Comment.objects.get(text=comment_form_data["text"])
        )
