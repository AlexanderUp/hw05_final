import os
import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Follow, Group, Post

User = get_user_model()

GROUP_INITIAL_FIELD_VALUES = {
    "title": "Test_group_title",
    "slug": "Test_group_slug",
    "description": "Test_group_description",
}
POST_INITIAL_FIELD_VALUES = {
    "text": "Test_post_text",
}

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class TemplatesUsedViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username="auth_user")
        cls.group = Group.objects.create(
            **GROUP_INITIAL_FIELD_VALUES
        )
        cls.post = Post.objects.create(
            **POST_INITIAL_FIELD_VALUES,
            author=cls.user,
            group=cls.group,
        )
        cls.templates_guest_access = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:group_list", kwargs={
                "slug": TemplatesUsedViewTest.group.slug
            }): "posts/group_list.html",
            reverse("posts:profile", kwargs={
                "username": TemplatesUsedViewTest.user.username
            }): "posts/profile.html",
            reverse("posts:post_detail", kwargs={
                "post_id": TemplatesUsedViewTest.post.pk
            }): "posts/post_detail.html",
        }
        cls.templates_authorized_access = {
            reverse("posts:post_create"): "posts/create_post.html",
            reverse("posts:follow_index"): "posts/follow.html",
        }
        cls.templates_authorized_post_author_access = {
            reverse("posts:post_edit", kwargs={
                "post_id": TemplatesUsedViewTest.post.pk
            }): "posts/create_post.html",
        }
        cls.templates_authorized_not_author_access = {
            reverse("posts:post_edit", kwargs={
                "post_id": TemplatesUsedViewTest.post.pk
            }): "posts/post_detail.html",
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TemplatesUsedViewTest.user)

    def test_views_use_correct_templates_authorized_client(self):
        """
        Проверяем, что для авторизованного пользователя view-функции
        используют корректные шаблоны. Данный пользователь является
        автором поста.
        """
        url_template_dict = {
            **TemplatesUsedViewTest.templates_guest_access,
            **TemplatesUsedViewTest.templates_authorized_access,
            **TemplatesUsedViewTest.templates_authorized_post_author_access,
        }
        for url, template in url_template_dict.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_views_use_correct_templates_guest_client(self):
        """
        Проверяем, что для неавторизованного пользователя view-функции
        используют корректные шаблоны.
        """
        url_template_dict = {
            **TemplatesUsedViewTest.templates_guest_access,
        }
        for url, template in url_template_dict.items():
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_views_use_correct_templates_guest_client_login_redirect(self):
        """
        Проверяем, что для неавторизованного пользователя view-функции при
        перенаправлении на страницу логина используют корректные шаблоны.
        """
        url_template_dict = {
            **TemplatesUsedViewTest.templates_authorized_access,
            **TemplatesUsedViewTest.templates_authorized_post_author_access,
        }
        for url, template in url_template_dict.items():
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertNotEqual(
                    TemplatesUsedViewTest.user.pk,
                    response.wsgi_request.user.pk
                )
                self.assertTrue(response.wsgi_request.user.is_anonymous)
                self.assertFalse(response.wsgi_request.user.is_authenticated)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                redirected_response = self.guest_client.get(
                    f"/auth/login/?next={url}"
                )
                self.assertEqual(
                    redirected_response.status_code, HTTPStatus.OK
                )
                self.assertTemplateNotUsed(redirected_response, template)
                self.assertTemplateUsed(
                    redirected_response, "users/login.html"
                )

    def test_post_detail_view_use_correct_template_authorized_author(self):
        """
        Проверяем, что авторизованному пользователю, являющемуся автором поста,
        возвращаются корректные шаблоны во view-функции.
        """
        url_template_dict = {
            **TemplatesUsedViewTest.templates_authorized_post_author_access,
        }
        self.assertEqual(
            TemplatesUsedViewTest.user.pk, TemplatesUsedViewTest.post.author.pk
        )
        for url, template in url_template_dict.items():
            with self.subTest(url=url, template=template):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    TemplatesUsedViewTest.user.pk,
                    response.wsgi_request.user.pk
                )
                self.assertFalse(response.wsgi_request.user.is_anonymous)
                self.assertTrue(response.wsgi_request.user.is_authenticated)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_post_detail_view_use_correct_template_authorized_not_author(self):
        """
        Проверяем, что залогиненому пользователю, не являющемуся автором поста,
        возвращаются корректные шаблоны во view-функции.
        """
        url_template_dict = {
            **TemplatesUsedViewTest.templates_authorized_not_author_access,
        }
        not_author = User.objects.create(username="Not_post_author")
        not_author_client = Client()
        not_author_client.force_login(not_author)
        self.assertNotEqual(not_author.pk, TemplatesUsedViewTest.user.pk)
        self.assertNotEqual(
            not_author.pk, TemplatesUsedViewTest.post.author.pk
        )

        for url, template in url_template_dict.items():
            with self.subTest(url=url, template=template):
                response = not_author_client.get(url)
                self.assertEqual(not_author.pk, response.wsgi_request.user.pk)
                self.assertFalse(response.wsgi_request.user.is_anonymous)
                self.assertTrue(response.wsgi_request.user.is_authenticated)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                redirect_url = f"/posts/{TemplatesUsedViewTest.post.pk}/"
                self.assertRedirects(response, redirect_url)
                redirected_response = not_author_client.get(redirect_url)
                self.assertTemplateUsed(redirected_response, template)


class ContextViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username="auth_user")
        cls.group = Group.objects.create(
            **GROUP_INITIAL_FIELD_VALUES,
        )
        cls.post = Post.objects.create(
            **POST_INITIAL_FIELD_VALUES,
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(ContextViewTest.user)

    def test_context_index(self):
        """
        Проверяем, что главная страница содержит объект Page.
        """
        response = self.authorized_client.get(reverse("posts:index"))
        page_object = response.context.get("page_obj")
        is_page_list = [
            isinstance(obj, Post) for obj in page_object.object_list
        ]
        self.assertIsNotNone(page_object)
        self.assertIsInstance(page_object, Page)
        self.assertIsNotNone(page_object.object_list)
        self.assertIsInstance(page_object.object_list, list)
        self.assertNotEqual(len(page_object.object_list), 0)
        self.assertTrue(all(is_page_list))

    def test_context_group_posts(self):
        """
        Проверяем, что страница группы содержит объект Page, Group, а все
        посты на ней принадлежат данной группе.
        """
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={
                "slug": GROUP_INITIAL_FIELD_VALUES["slug"]
            })
        )
        obj_list = response.context.get("page_obj").object_list
        is_posts_response_obj_list = [
            isinstance(obj, Post) for obj in obj_list
        ]
        is_posts_slugs_equal_to_fixture_slug = [
            bool(obj.group == ContextViewTest.group) for obj in obj_list
        ]
        self.assertIsNotNone(response.context.get("group"))
        self.assertIsInstance(response.context.get("group"), Group)
        self.assertEqual(
            response.context.get("group").title,
            GROUP_INITIAL_FIELD_VALUES["title"]
        )
        self.assertEqual(
            response.context.get("group").slug,
            GROUP_INITIAL_FIELD_VALUES["slug"]
        )
        self.assertEqual(
            response.context.get("group").description,
            GROUP_INITIAL_FIELD_VALUES["description"]
        )
        self.assertIsNotNone(response.context.get("page_obj"))
        self.assertIsInstance(response.context.get("page_obj"), Page)
        self.assertTrue(all(is_posts_response_obj_list))
        self.assertTrue(all(is_posts_slugs_equal_to_fixture_slug))

    def test_context_profile(self):
        """
        Проверяем контекст страницы профиля пользователя.
        """
        url = reverse("posts:profile", kwargs={
            "username": ContextViewTest.user.username,
        })
        response = self.guest_client.get(url)
        requested_user = response.context.get("requested_user")
        self.assertIsInstance(requested_user, User)
        self.assertEqual(requested_user, ContextViewTest.user)

        page = response.context.get("page_obj")
        self.assertIsInstance(page, Page)
        self.assertNotEqual(len(page.object_list), 0)
        is_correct_user_posts_responded = [
            (obj.author == ContextViewTest.user) for obj in page.object_list
        ]
        self.assertTrue(all(is_correct_user_posts_responded))

    def test_context_values_post_detail(self):
        """
        Проверяем, что контекст запроса указанного поста содержит корректные
        значения полей.
        """
        url = reverse(
            "posts:post_detail", kwargs={
                "post_id": ContextViewTest.post.pk
            }
        )
        response = self.authorized_client.get(url)
        self.assertIsInstance(response.context.get("post"), Post)
        self.assertEqual(
            response.context["post"].text,
            POST_INITIAL_FIELD_VALUES["text"]
        )
        self.assertEqual(
            response.context["post"].pub_date, ContextViewTest.post.pub_date
        )
        self.assertEqual(
            response.context.get("post").author, ContextViewTest.user
        )
        self.assertEqual(
            response.context.get("post").group, ContextViewTest.group
        )
        self.assertIsInstance(
            response.context["comment_form"], CommentForm
        )
        self.assertIsNotNone(response.context["comments"])

    def test_context_fields_post_detail(self):
        """
        Проверяем, что контекст запроса указанного поста содержит
        корректные типы полей.
        """
        fields_types_dict = {
            "text": models.TextField,
            "pub_date": models.DateTimeField,
            "author": models.ForeignKey,
            "group": models.ForeignKey,
        }

        response = self.authorized_client.get(
            reverse(
                "posts:post_detail", kwargs={
                    "post_id": ContextViewTest.post.pk
                }
            )
        )
        for field, expected_type in fields_types_dict.items():
            with self.subTest(field=field, expected_type=expected_type):
                self.assertIsInstance(
                    response.context["post"]._meta.get_field(field),
                    expected_type
                )

    def test_context_post_create(self):
        """
        Проверяем наличине формы поста на странице создания поста.
        """
        url = reverse("posts:post_create")
        response = self.authorized_client.get(url)
        form_obj = response.context.get("form")
        self.assertIsInstance(form_obj, PostForm)

    def test_context_post_edit(self):
        """
        Проверяем контекст страницы редактирования поста.
        """
        url = reverse("posts:post_edit", kwargs={
            "post_id": ContextViewTest.post.pk,
        })
        response = self.authorized_client.get(url)
        form_obj = response.context.get("form")
        self.assertIsInstance(form_obj, PostForm)
        is_edit_obj = response.context.get("is_edit")
        self.assertIsInstance(is_edit_obj, bool)

    def test_context_follow_index(self):
        """
        Проверяем контекст страницы с постами друзей.
        """
        user_follower = User.objects.create(username="follower")
        Follow.objects.create(
            user=user_follower, author=ContextViewTest.user
        )
        user_follower_client = Client()
        user_follower_client.force_login(user_follower)
        url = reverse("posts:follow_index")
        response = user_follower_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        page_obj = response.context.get("page_obj")
        self.assertIsInstance(page_obj, Page)
        followed_users = user_follower.follower.values("author").all()
        total_follow_post_count = Post.objects.filter(
            author__in=followed_users,
        ).count()
        self.assertEqual(page_obj.paginator.count, total_follow_post_count)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="auth_user")
        cls.group = Group.objects.create(
            **GROUP_INITIAL_FIELD_VALUES
        )
        cls.test_posts_count = 13
        posts = [
            Post(
                text="_".join(
                    (POST_INITIAL_FIELD_VALUES["text"], str(i))
                ),
                author=cls.user,
                group=cls.group
            ) for i in range(cls.test_posts_count)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def _test_paginator(self, page_object, post_count, url):
        """
        Вспомогательный метод для тестирования пагинации.
        Проверяем следующее:
        - объект контекста - экземпляр класса Page;
        - все объекты на странице - экземпляры класса Post;
        - атрибут объекта контекста - список с не равной нулю длиной;
        - количество объектов на первой и последней страницах,
        возвращенных пагинатором.
        """
        is_page_instance_list = [
            isinstance(obj, Post) for obj in page_object.object_list
        ]
        self.assertIsNotNone(page_object)
        self.assertIsInstance(page_object, Page)
        self.assertIsNotNone(page_object.object_list)
        self.assertIsInstance(page_object.object_list, list)
        self.assertNotEqual(len(page_object.object_list), 0)
        self.assertTrue(all(is_page_instance_list))
        if post_count > settings.NUMBER_OF_POSTS_PER_PAGE:
            last_page_number = (
                (post_count // settings.NUMBER_OF_POSTS_PER_PAGE) + 1
            )
            last_page_posts_count = (
                post_count % settings.NUMBER_OF_POSTS_PER_PAGE
            )
            response_last_page = self.guest_client.get(
                url + f"?page={last_page_number}"
            )
            self.assertEqual(
                len(page_object.object_list),
                settings.NUMBER_OF_POSTS_PER_PAGE
            )
            self.assertEqual(
                len(response_last_page.context.get("page_obj").object_list),
                last_page_posts_count
            )
        else:
            self.assertEqual(
                len(page_object.object_list),
                post_count
            )

    def test_index_page_paginator(self):
        """
        Тестируем пагинацию на главной странице проекта.
        """
        url_name = "posts:index"
        url = reverse(url_name)
        response = self.guest_client.get(url)
        page_object = response.context.get("page_obj")
        post_count = Post.objects.count()
        self._test_paginator(page_object, post_count, url)

    def test_group_list_paginator(self):
        """
        Тестируем пагинацию на странице конкретной группы.
        """
        url_name = "posts:group_list"
        url = reverse(url_name, kwargs={"slug": ContextViewTest.group.slug})
        response = self.guest_client.get(url)
        page_object = response.context.get("page_obj")
        post_count = ContextViewTest.group.posts.count()
        self._test_paginator(page_object, post_count, url)

    def test_profile_page_paginator(self):
        """
        Тестируем пагинацию на странице конкретного пользователя.
        """
        url_name = "posts:profile"
        url = reverse(url_name, kwargs={
            "username": ContextViewTest.user.username
        })
        response = self.guest_client.get(url)
        page_object = response.context.get("page_obj")
        post_count = ContextViewTest.user.posts.count()
        self._test_paginator(page_object, post_count, url)


class PostCreationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="auth_user")
        cls.group_primary = Group.objects.create(
            title="Test_group_primary",
            slug="Primary_group",
            description="Test_primary_group_description",
        )
        cls.group_secondary = Group.objects.create(
            title="Test_group_secondary",
            slug="Secondary_group",
            description="Test_secondary_group_description",
        )
        cls.post = Post.objects.create(
            **POST_INITIAL_FIELD_VALUES,
            author=cls.user,
            group=cls.group_primary,
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreationTest.user)

    def test_post_is_on_main_page(self):
        """
        Проверяем, что созданный пост отображается на главной странице.
        """
        url = reverse("posts:index")
        response = self.authorized_client.get(url)
        post_lists = response.context.get("page_obj").object_list
        self.assertIn(PostCreationTest.post, post_lists)

    def test_post_is_on_profile_page(self):
        """
        Проверяем, что созданный пост отображается на странице пользователя.
        """
        url = reverse("posts:profile", kwargs={
            "username": PostCreationTest.user.username,
        })
        response = self.authorized_client.get(url)
        post_object_list = response.context.get("page_obj").object_list
        self.assertIn(PostCreationTest.post, post_object_list)

    def test_post_is_on_group_page(self):
        """
        Проверяем, что созданный пост отображается на странице присвоенной
        ему группы группы.
        """
        url = reverse("posts:group_list", kwargs={
            "slug": PostCreationTest.group_primary.slug,
        })
        response = self.authorized_client.get(url)
        post_object_list = response.context.get("page_obj").object_list
        self.assertIn(PostCreationTest.post, post_object_list)

    def test_post_is_not_on_incorrect_group_page(self):
        """
        Проверяем, что созданный пост не отображается на странице группы,
        не являющейся присвоенной ему.
        """
        url = reverse("posts:group_list", kwargs={
            "slug": PostCreationTest.group_secondary.slug,
        })
        response = self.authorized_client.get(url)
        post_object_list = response.context.get("page_obj").object_list
        self.assertNotIn(PostCreationTest.post, post_object_list)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageCreationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="auth_user")
        cls.group = Group.objects.create(
            **GROUP_INITIAL_FIELD_VALUES
        )
        cls.binary_content = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00"
            b"\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        cls.post = Post.objects.create(
            text=POST_INITIAL_FIELD_VALUES["text"],
            author=cls.user,
            group=cls.group,
            image=SimpleUploadedFile(
                "file.gif",
                cls.binary_content,
                content_type="image/gif",
            )
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(ImageCreationTest.user)

    def test_is_post_created(self):
        """
        Проверяем, что тестовый пост с изображением создан в БД.
        """
        initial_post_count = Post.objects.count()
        self.assertEqual(initial_post_count, 1)
        post = get_object_or_404(Post, pk=ImageCreationTest.post.pk)
        self.assertIsNotNone(post.image)
        self.assertIsInstance(post.image, ImageFieldFile)
        self.assertTrue(os.path.exists(post.image.path))
        with open(post.image.path, "br") as f:
            content = f.read()
            self.assertEqual(content, ImageCreationTest.binary_content)

    def test_image_is_in_paginated_page_context(self):
        """
        Проверяем, что при выводе страницы с постами с картинками в контексте
        пагинатора передаются посты с картинками.
        """
        urls = (
            reverse("posts:index"),
            reverse("posts:group_list", args=(ImageCreationTest.group.slug,)),
            reverse("posts:profile", args=(ImageCreationTest.user.username,)),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get("page_obj")
                im_obj = page_obj.object_list[0].image
                self.assertIsNotNone(im_obj)
                self.assertIsInstance(im_obj, ImageFieldFile)
                self.assertEqual(
                    im_obj.name, ImageCreationTest.post.image.name
                )

    def test_image_is_in_post_detail_page_context(self):
        """
        Проверяем, что при выводе страницы с постом в контексте содержится
        картинка.
        """
        url = reverse("posts:post_detail", args=(ImageCreationTest.post.pk,))
        response = self.guest_client.get(url)
        post_obj = response.context.get("post")
        self.assertIsNotNone(post_obj.image)
        self.assertIsInstance(post_obj.image, ImageFieldFile)
        self.assertEqual(
            post_obj.image.name, ImageCreationTest.post.image.name
        )


class CommentCreationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="auth_user")
        cls.group = Group.objects.create(
            **GROUP_INITIAL_FIELD_VALUES
        )
        cls.post = Post.objects.create(
            **POST_INITIAL_FIELD_VALUES,
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(CommentCreationTest.user)

    def test_guest_client_redirect(self):
        """
        Проверяем, что неавторизованный пользователь перенаправляется
        на страницу авторизации.
        """
        initial_comment_count = CommentCreationTest.post.comments.count()
        self.assertEqual(initial_comment_count, 0)
        response = self.guest_client.post(
            reverse("posts:add_comment", args=(CommentCreationTest.post.pk,))
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        redirected_url = (
            f"/auth/login/?next=/posts/{CommentCreationTest.post.pk}/comment/"
        )
        self.assertRedirects(response, redirected_url)
        self.assertEqual(
            CommentCreationTest.post.comments.count(), initial_comment_count
        )

    def test_created_comment_appears_on_post_page(self):
        """
        Проверяем, что созданный комментарий появляется на странице поста.
        """
        comment_form_data = {
            "text": "Comment text",
        }
        initial_post_comment_count = CommentCreationTest.post.comments.count()
        initial_user_comment_count = CommentCreationTest.user.comments.count()
        self.assertEqual(initial_post_comment_count, 0)
        self.assertEqual(initial_user_comment_count, 0)

        response = self.auth_client.post(
            reverse("posts:add_comment", args=(CommentCreationTest.post.pk,)),
            data=comment_form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                "posts:post_detail", args=(CommentCreationTest.post.pk,)
            )
        )
        self.assertEqual(
            CommentCreationTest.post.comments.count(),
            (initial_post_comment_count + 1)
        )
        self.assertEqual(
            CommentCreationTest.user.comments.count(),
            (initial_user_comment_count + 1)
        )
        new_response = self.auth_client.get(
            reverse("posts:post_detail", args=(CommentCreationTest.post.pk,))
        )
        comments = new_response.context.get("comments")
        self.assertIsNotNone(comments)
        comment = CommentCreationTest.user.comments.get(
            text=comment_form_data.get("text")
        )
        self.assertIn(comment, comments)


class CachingIndexPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="auth_user")
        cls.group = Group.objects.create(
            **GROUP_INITIAL_FIELD_VALUES
        )
        cls.initial_post_count = 8
        cls.test_text = "test_caching_text_{}"
        posts = [
            Post(
                text=cls.test_text.format(i),
                author=cls.user,
                group=cls.group,
            ) for i in range(cls.initial_post_count)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_cache_new_exist_post_does_not_appear_on_index_page(self):
        """
        Проверяем работу кеша - после удаления поста из БД он все равно
        отображается на странице пока не устареет кеш.
        """
        self.assertEqual(
            Post.objects.count(), CachingIndexPageTest.initial_post_count
        )
        url = reverse("posts:index")
        response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            len(response.context.get("page_obj").object_list),
            CachingIndexPageTest.initial_post_count
        )
        Post.objects.get(pk=CachingIndexPageTest.initial_post_count).delete()
        self.assertEqual(
            Post.objects.count(),
            (CachingIndexPageTest.initial_post_count - 1)
        )
        second_response = self.guest_client.get(url)
        self.assertEqual(second_response.status_code, HTTPStatus.OK)
        self.assertEqual(response.content, second_response.content)
        test_string = CachingIndexPageTest.test_text.format(
            CachingIndexPageTest.initial_post_count - 1
        ).encode()
        self.assertIn(test_string, second_response.content)
        cache.clear()
        third_response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(response.content, third_response.content)
        self.assertNotIn(test_string, third_response.content)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="Follower")
        cls.author = User.objects.create(username="Author")
        cls.group = Group.objects.create(**GROUP_INITIAL_FIELD_VALUES)
        cls.post = Post.objects.create(
            **POST_INITIAL_FIELD_VALUES,
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.auth_client = Client()
        self.auth_client.force_login(TestFollow.user)

    def test_follow_user(self):
        """
        Проверяем, что при подписке на автора создается соответствующая запись
        в БД.
        """
        initial_follow_entry_count = Follow.objects.count()
        self.assertEqual(initial_follow_entry_count, 0)
        url = reverse(
            "posts:profile_follow", args=(TestFollow.author.username,)
        )
        response = self.auth_client.get(url)
        self.assertRedirects(
            response, reverse(
                "posts:profile", args=(TestFollow.author.username,)
            )
        )
        self.assertEqual(
            Follow.objects.count(), (initial_follow_entry_count + 1)
        )
        self.assertEqual(
            TestFollow.user.follower.count(), (initial_follow_entry_count + 1)
        )
        self.assertEqual(
            TestFollow.author.following.count(),
            (initial_follow_entry_count + 1)
        )

    def test_unfollow_user(self):
        """
        Проверяем, что при отписке от автора соответствующая запись в БД
        удаляется.
        """
        Follow.objects.create(
            user=TestFollow.user,
            author=TestFollow.author,
        )
        initial_follow_entry_count = Follow.objects.count()
        self.assertEqual(initial_follow_entry_count, 1)
        url = reverse(
            "posts:profile_unfollow", args=(TestFollow.author.username,)
        )
        response = self.auth_client.get(url)
        self.assertRedirects(
            response, reverse(
                "posts:profile", args=(TestFollow.author.username,)
            )
        )
        self.assertEqual(
            Follow.objects.count(), (initial_follow_entry_count - 1)
        )
        self.assertEqual(
            TestFollow.user.follower.count(), (initial_follow_entry_count - 1)
        )
        self.assertEqual(
            TestFollow.author.following.count(),
            (initial_follow_entry_count - 1)
        )

    def test_post_is_in_follow_index_page(self):
        """
        Проверяем, что посты автора из списка подписок есть на странице.
        """
        Follow.objects.create(
            user=TestFollow.user,
            author=TestFollow.author,
        )
        self.assertEqual(TestFollow.user.follower.count(), 1)
        self.assertEqual(TestFollow.author.following.count(), 1)
        url = reverse("posts:follow_index")
        response = self.auth_client.get(url)
        self.assertEqual(len(response.context.get("page_obj").object_list), 1)
        page = response.context.get("page_obj")
        followed_user = TestFollow.user.follower.values("author")
        post_by_followed_count = Post.objects.filter(
            author__in=followed_user
        ).count()
        self.assertEqual(page.paginator.count, post_by_followed_count)

    def test_post_is_not_in_follow_index_page(self):
        """
        Проверяем, что среди постов из списка подписок не отображаются
        посты авторов, на которые пользователь не подписан.
        """
        self.assertEqual(TestFollow.user.posts.count(), 0)
        self.assertEqual(TestFollow.author.posts.count(), 1)
        Follow.objects.create(
            user=TestFollow.user,
            author=TestFollow.author,
        )
        self.assertEqual(TestFollow.user.follower.count(), 1)
        self.assertEqual(TestFollow.author.following.count(), 1)

        client_author = Client()
        client_author.force_login(TestFollow.author)
        url = reverse("posts:follow_index")
        response = client_author.get(url)
        self.assertEqual(len(response.context.get("page_obj").object_list), 0)
