from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.IndexListView.as_view(), name="index"),
    path("follow/", views.FollowIndexListView.as_view(), name="follow_index"),
    path(
        "group/<slug:slug>/",
        views.GroupPostsListView.as_view(),
        name="group_list"
    ),
    path(
        "profile/<str:username>/",
        views.ProfileListView.as_view(),
        name="profile"
    ),
    path(
        "profile/<str:username>/follow/",
        views.profile_follow,
        name="profile_follow"
    ),
    path(
        "profile/<str:username>/unfollow/",
        views.profile_unfollow,
        name="profile_unfollow"
    ),
    path("create/", views.PostCreateView.as_view(), name="post_create"),
    path(
        "posts/<int:pk>/", views.PostDetailView.as_view(), name="post_detail"
    ),
    path(
        "posts/<int:pk>/edit/",
        views.PostUpdateView.as_view(),
        name="post_edit"
    ),
    path(
        "posts/<int:pk>/delete/",
        views.PostDeleteView.as_view(),
        name="post_delete"
    ),
    path(
        "posts/<int:pk>/comment/",
        views.CommentCreateView.as_view(),
        name="add_comment"
    ),
    path(
        "posts/<int:pk>/comment/<int:comment_pk>/edit/",
        views.CommentUpdateView.as_view(),
        name="comment_edit"
    ),
    path(
        "posts/<int:pk>/comment/<int:comment_pk>/delete/",
        views.CommentDeleteView.as_view(),
        name="comment_delete"
    ),
]
