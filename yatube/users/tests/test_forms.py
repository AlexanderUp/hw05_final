from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestSignUp(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_user_creation(self):
        """
        Проверяем, что после отправки формы регистрации нового
        пользователя, новый пользователь создается в БД.
        """
        form_full_data = {
            "first_name": "new_user_first_name",
            "last_name": "new_user_last_name",
            "username": "new_user_username",
            "email": "new_user_email@example.com",
            "password1": "f1baccdd6d64690fec2f",
            "password2": "f1baccdd6d64690fec2f",
        }
        initial_user_count = User.objects.count()
        self.assertEqual(initial_user_count, 0)
        response = self.guest_client.post(
            reverse("users:signup"),
            data=form_full_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(User.objects.filter(
            username=form_full_data["username"]
        ).exists())
        self.assertRedirects(response, reverse("posts:index"))
        self.assertEqual(User.objects.count(), initial_user_count + 1)

    def test_signup_user_creation_invalid_form_password_field(self):
        """
        Проверяем, что после отправки некорректной формы регистрации
        нового пользователя вызывается ошибка валидации формы.
        """
        form_full_data_invalid = {
            "first_name": "new_user_first_name",
            "last_name": "new_user_last_name",
            "username": "new_user_username",
            "email": "new_user_email@example.com",
            "password1": "f1baccdd6d64690fec2f",
            "password2": "f1baccdd",
        }
        initial_user_count = User.objects.count()
        self.assertEqual(initial_user_count, 0)
        response = self.guest_client.post(
            reverse("users:signup"),
            data=form_full_data_invalid,
            follow=True
        )
        self.assertFalse(User.objects.filter(
            username=form_full_data_invalid["username"]
        ).exists())
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertFormError(
            response,
            "form",
            "password2",
            "Два поля с паролями не совпадают."
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_signup_user_creation_invalid_form_user_existed(self):
        """
        Проверяем, что после отправки некорректной формы регистрации
        нового пользователя вызывается ошибка валидации формы.
        """
        self.assertEqual(User.objects.count(), 0)
        user = User.objects.create(username="Existed_user")
        initial_user_count = User.objects.count()
        self.assertEqual(initial_user_count, 1)
        form_full_data_invalid = {
            "first_name": "new_user_first_name",
            "last_name": "new_user_last_name",
            "username": user.username,
            "email": "new_user_email@example.com",
            "password1": "f1baccdd6d64690fec2f",
            "password2": "f1baccdd6d64690fec2f",
        }

        response = self.guest_client.post(
            reverse("users:signup"),
            data=form_full_data_invalid,
            follow=True
        )
        self.assertFormError(
            response,
            "form",
            "username",
            "Пользователь с таким именем уже существует."
        )
        self.assertEqual(User.objects.count(), initial_user_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
