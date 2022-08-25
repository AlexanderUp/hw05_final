from django.contrib.auth import views as django_auth_view
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("login/",
         django_auth_view.LoginView.as_view(template_name="users/login.html"),
         name='login'),
    path("logout/",
         django_auth_view.LogoutView.as_view(
             template_name="users/logged_out.html"
         ),
         name="logout"),
    path("password_change/",
         django_auth_view.PasswordChangeView.as_view(
             template_name="users/password_change_form.html"
         ),
         name="password_change_form"),
    path("password_change/done/",
         django_auth_view.PasswordChangeDoneView.as_view(
             template_name="users/password_change_done.html"
         ),
         name="password_change_done"),
    path("password_reset/",
         django_auth_view.PasswordResetView.as_view(
             template_name="users/password_reset_form.html"
         ),
         name="password_reset"),
    path("password_reset/done/",
         django_auth_view.PasswordResetDoneView.as_view(
             template_name="users/password_reset_done.html"
         ),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         django_auth_view.PasswordResetConfirmView.as_view(
             template_name="users/password_reset_confirm.html"
         ),
         name="password_reset_confirm"),
    path("reset/done/",
         django_auth_view.PasswordResetCompleteView.as_view(
             template_name="users/password_reset_complete.html"
         ),
         name="password_reset_complete"),
]
