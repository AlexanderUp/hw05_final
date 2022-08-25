from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestAboutURLs(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="User_No_Name")
        cls.urls_templates_dict = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TestAboutURLs.user)

    def test_urls_correct_templates(self):
        """
        Проверяем, что в приложении <about> указанные адреса используют
        указанные шаблоны для авторизованного и неавторизованного
        пользователей и возвращают корректные статус-коды.
        """
        for url, template_name in TestAboutURLs.urls_templates_dict.items():
            with self.subTest(url=url, template_name=template_name):
                guest_response = self.guest_client.get(url)
                self.assertEqual(guest_response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(guest_response, template_name)

                authorized_response = self.authorized_client.get(url)
                self.assertEqual(
                    authorized_response.status_code, HTTPStatus.OK
                )
                self.assertTemplateUsed(authorized_response, template_name)


class TestAboutTemplates(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="User_No_Name")
        cls.urls_templates_dict = {
            reverse("about:author"): "about/author.html",
            reverse("about:tech"): "about/tech.html",
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TestAboutTemplates.user)

    def test_views_use_correct_templates_(self):
        for url, template in TestAboutTemplates.urls_templates_dict.items():
            with self.subTest(url=url, template=template):
                response_guest = self.guest_client.get(url)
                self.assertTemplateUsed(response_guest, template)

                response_auth = self.authorized_client.get(url)
                self.assertTemplateUsed(response_auth, template)
