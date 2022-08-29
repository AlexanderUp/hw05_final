from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.IndexListView.as_view(), name="index"),
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
        "posts/<int:pk>/comment/",
        views.AddCommentView.as_view(),
        name="add_comment"
    ),
    path(
        "posts/<int:pk>/edit/", views.PostEditView.as_view(), name="post_edit"
    ),
    path(
        "posts/<int:pk>/", views.PostDetailView.as_view(), name="post_detail"
    ),
    path("create/", views.PostCreateView.as_view(), name="post_create"),
    path("follow/", views.FollowIndexListView.as_view(), name="follow_index"),
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
]
