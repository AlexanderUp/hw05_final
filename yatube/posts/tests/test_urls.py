from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        guest_client = Client()
        response = guest_client.get("/")
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="Test_User")
        cls.group = Group.objects.create(
            title="Test_Group",
            slug="test_group_slug",
            description="Test group",
        )
        cls.post = Post.objects.create(
            text="Test text",
            author=cls.user,
            group=cls.group,
        )
        username = PostsURLTests.user.username
        slug = PostsURLTests.group.slug
        post_id = PostsURLTests.post.id

        cls.url_template_names_guest_access = {
            "/": "posts/index.html",
            f"/group/{slug}/": "posts/group_list.html",
            f"/profile/{username}/": "posts/profile.html",
            f"/posts/{post_id}/": "posts/post_detail.html",
        }
        cls.url_template_names_auth_access = {
            "/create/": "posts/create_post.html",
            "/follow/": "posts/follow.html",
        }
        cls.url_template_names_auth_author_access = {
            f"/posts/{post_id}/edit/": "posts/create_post.html",
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_user_is_post_author(self):
        """
        Проверяем, что созданный в фикстурах пользователь является
        автором созданного в фикстурах поста.
        """
        self.assertEqual(PostsURLTests.user.pk, PostsURLTests.post.author.pk)

    def test_authorized_user_urls_use_correct_template(self):
        """
        Проверяем, что при отображении страниц для авторизованного
        пользователя используются правильные шаблоны и возвращаются
        корректные статус-коды.
        """
        url_templates_names = {
            **PostsURLTests.url_template_names_guest_access,
            **PostsURLTests.url_template_names_auth_access,
            **PostsURLTests.url_template_names_auth_author_access,
        }

        for url, template_name in url_templates_names.items():
            with self.subTest(url=url, template_name=template_name):
                response = self.authorized_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template_name)

    def test_guest_user_urls_use_correct_template(self):
        """
        Проверяем, что при отображении не требующих авторизации страниц
        для неавторизованного пользователя используются правильные шаблоны
        и возвращаются корректные статус-коды.
        """
        for url, template_name in (
            PostsURLTests.url_template_names_guest_access.items()
        ):
            with self.subTest(url=url, template_name=template_name):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template_name)

    def test_guest_user_login_required_redirect(self):
        """
        Проверяем, что неавторизованный пользователь перенаправляется
        на страницу авторизации. Проверка осуществляется методом
        определения является ли используемый шаблон шаблоном страницы
        авторизации.
        """
        login_required_urls = {
            **PostsURLTests.url_template_names_auth_access,
            **PostsURLTests.url_template_names_auth_author_access,
        }
        for url, template_name in login_required_urls.items():
            with self.subTest(url=url, template_name=template_name):
                response = self.guest_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, "users/login.html")
                self.assertRedirects(response, f"/auth/login/?next={url}")

    def test_authorized_not_author_post_edit_url(self):
        """
        Проверяем, что авторизованный пользователь, не являющийся автором
        поста, получает не шаблон редактированя поста, а шаблон просмотра
        поста.
        """
        not_author_user = User.objects.create(username="Not_post_author")
        self.assertNotEqual(not_author_user.pk, PostsURLTests.user.pk)
        self.assertNotEqual(not_author_user.pk, PostsURLTests.post.author.pk)

        authorized_not_author_client = Client()
        authorized_not_author_client.force_login(not_author_user)
        urls = PostsURLTests.url_template_names_auth_author_access
        for url, template_name in urls.items():
            with self.subTest(url=url, template_name=template_name):
                response = authorized_not_author_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateNotUsed(response, template_name)
                self.assertTemplateUsed(response, "posts/post_detail.html")

    def test_url_does_not_exist(self):
        """
        Проверяем запрос к несуществующей странице.
        """
        url = "/page_url_that_does_not_exists/"
        authorized_client_response = self.authorized_client.get(url)
        self.assertEqual(
            authorized_client_response.status_code, HTTPStatus.NOT_FOUND
        )
        self.assertTemplateUsed(authorized_client_response, "core/404.html")

        guest_client_response = self.guest_client.get(url)
        self.assertEqual(
            guest_client_response.status_code, HTTPStatus.NOT_FOUND
        )
        self.assertTemplateUsed(guest_client_response, "core/404.html")
