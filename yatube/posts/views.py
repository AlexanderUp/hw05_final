from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import get_page_object_from_paginator

User = get_user_model()


@cache_page(20)
@vary_on_cookie
def index(request):
    posts = (Post.objects
                 .select_related("author")
                 .all())
    page_obj = get_page_object_from_paginator(
        posts, settings.NUMBER_OF_POSTS_PER_PAGE, request
    )
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author").all()
    page_obj = get_page_object_from_paginator(
        posts, settings.NUMBER_OF_POSTS_PER_PAGE, request
    )
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    requested_user = get_object_or_404(User, username=username)
    posts = requested_user.posts.all()
    page_obj = get_page_object_from_paginator(
        posts, settings.NUMBER_OF_POSTS_PER_PAGE, request
    )
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=requested_user
    ).exists()
    context = {
        "requested_user": requested_user,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comment_form = CommentForm()
    comments = post.comments.select_related("author").all()
    context = {
        "post": post,
        "comment_form": comment_form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect("posts:profile", username=request.user.username)
    context = {
        "form": form,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.pk != post.author.pk:
        return HttpResponseRedirect(
            reverse("posts:post_detail", args=(post_id,))
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(
            reverse("posts:post_detail", args=(post_id,))
        )
    context = {
        "form": form,
        "is_edit": True,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_object_from_paginator(
        posts, settings.NUMBER_OF_POSTS_PER_PAGE, request
    )
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follow_exists = Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    if request.user != author and is_follow_exists:
        Follow.objects.filter(
            user=request.user,
            author=author,
        ).delete()
    return redirect("posts:profile", username=username)
