from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class TestURLsUserApp(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="User_No_Name")
        cls.urls = {
            "/auth/signup/": "users/signup.html",
            "/auth/login/": "users/login.html",
            "/auth/password_reset/": "users/password_reset_form.html",
            "/auth/password_reset/done/": "users/password_reset_done.html",
            "/auth/reset/done/": "users/password_reset_complete.html",
            "/auth/reset/<uidb64>/<token>/":
            "users/password_reset_confirm.html",
            "/auth/logout/": "users/logged_out.html",
        }
        cls.urls_login_required = {
            "/auth/password_change/": "users/password_change_form.html",
            "/auth/password_change/done/": "users/password_change_done.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TestURLsUserApp.user)

    def test_urls_use_correct_templates(self):
        """
        Проверяем, что для авторизованного и неавторизованного пользователей
        используются верные шаблоны и возвращаются верные статус-коды.
        """
        for url, template_name in TestURLsUserApp.urls.items():
            with self.subTest(url=url, template_name=template_name):
                guest_response = self.guest_client.get(url)
                self.assertEqual(guest_response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(guest_response, template_name)

                auth_response = self.authorized_client.get(url)
                self.assertEqual(auth_response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(auth_response, template_name)

    def test_login_required_urls_use_correct_templates(self):
        """
        Проверяем, что пользователь получает корректный ответ при запросе
        страницы, требующей авторизации.
        """
        for url, template_name in TestURLsUserApp.urls_login_required.items():
            with self.subTest(url=url, template_name=template_name):
                guest_response = self.guest_client.get(url)
                self.assertEqual(guest_response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(
                    guest_response, f"/auth/login/?next={url}"
                )
                guest_response = self.guest_client.get(
                    f"/auth/login/?next={url}"
                )
                self.assertEqual(guest_response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(guest_response, "users/login.html")

                auth_response = self.authorized_client.get(url)
                self.assertTrue(TestURLsUserApp.user.is_authenticated)
                self.assertEqual(auth_response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(auth_response, template_name)
