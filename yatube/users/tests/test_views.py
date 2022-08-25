from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CreationForm

User = get_user_model()


class TestViewUserApp(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="User_No_Name")
        cls.urls = {
            "users:signup": "users/signup.html",
            "users:login": "users/login.html",
            "users:password_reset": "users/password_reset_form.html",
            "users:password_reset_done": "users/password_reset_done.html",
            "users:password_reset_complete":
            "users/password_reset_complete.html",
            "users:logout": "users/logged_out.html",
        }
        cls.urls_login_required = {
            "users:password_change_form": "users/password_change_form.html",
            "users:password_change_done": "users/password_change_done.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TestViewUserApp.user)

    def test_urls_use_correct_templates(self):
        """
        Проверяем, что для авторизованного и неавторизованного пользователей
        используются верные шаблоны.
        """
        for url_name, template_name in TestViewUserApp.urls.items():
            with self.subTest(url_name=url_name, template_name=template_name):
                url = reverse(url_name)
                guest_response = self.guest_client.get(url)
                self.assertTemplateUsed(guest_response, template_name)

                authorized_response = self.authorized_client.get(url)
                self.assertTemplateUsed(authorized_response, template_name)

    def test_auth_required_urls_use_correct_templates(self):
        """
        Проверяем, что залогиненного пользователя используются корректные
        шаблоны.
        """
        for url_name, template in TestViewUserApp.urls_login_required.items():
            with self.subTest(url_name=url_name, template=template):
                url = reverse(url_name)
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_password_reset_token_use_correct_template(self):
        """
        Проверяем, что view-функция сброса пароля использует корректный шаблон.
        """
        url_name = "users:password_reset_confirm"
        template = "users/password_reset_confirm.html"
        url = reverse(url_name, kwargs={
            "uidb64": 'random_string',
            "token": 'random_token',
        })
        response = self.guest_client.get(url)
        self.assertTemplateUsed(response, template)

    def test_signup_page_context_use_correct_form(self):
        """
        Проверяем, что в контексте страницы регистрации нового пользователя
        передается корректная форма для создания нового пользователя.
        """
        response = self.guest_client.get(reverse("users:signup"))
        form_obj = response.context.get("form")
        self.assertIsNotNone(form_obj)
        self.assertIsInstance(form_obj, CreationForm)
