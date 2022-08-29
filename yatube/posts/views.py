from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


@method_decorator(cache_page(20), name='dispatch')
@method_decorator(vary_on_cookie, name='dispatch')
class IndexListView(ListView):
    template_name = "posts/index.html"
    paginate_by = settings.NUMBER_OF_POSTS_PER_PAGE

    def get_queryset(self):
        return Post.objects.select_related("author", "group").all()


class GroupPostsListView(ListView):
    template_name = "posts/group_list.html"
    paginate_by = settings.NUMBER_OF_POSTS_PER_PAGE

    def get_queryset(self):
        self.group = get_object_or_404(Group, slug=self.kwargs["slug"])
        return self.group.posts.select_related("author").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = self.group
        return context


class ProfileListView(ListView):
    template_name = "posts/profile.html"
    paginate_by = settings.NUMBER_OF_POSTS_PER_PAGE

    def get_queryset(self):
        self.requested_user = get_object_or_404(
            User, username=self.kwargs["username"]
        )
        return self.requested_user.posts.select_related("group").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["requested_user"] = self.requested_user
        context["following"] = (
            self.request.user.is_authenticated and Follow.objects.filter(
                user=self.request.user, author=self.requested_user
            ).exists()
        )
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"

    def get_object(self):
        return Post.objects.select_related("group").get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["comments"] = (
            self.object.comments.select_related("author").all()
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ["text", "group", "image", ]
    template_name = "posts/create_post.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "posts:profile", args=(self.request.user.username,)
        )


class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ["text", "group", "image", ]
    template_name = "posts/create_post.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user.is_authenticated:
            if request.user != self.object.author:
                return redirect(
                    reverse("posts:post_detail", args=(self.kwargs.get("pk"),))
                )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context


class AddCommentView(LoginRequiredMixin, FormView):
    form_class = CommentForm

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs.get("pk"))
        form = self.form_class(request.POST)
        if form.is_valid:
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
        return redirect("posts:post_detail", pk=kwargs.get("pk"))


@method_decorator(login_required, name='dispatch')
class FollowIndexListView(ListView):
    template_name = "posts/follow.html"
    paginate_by = settings.NUMBER_OF_POSTS_PER_PAGE

    def get_queryset(self):
        return (
            Post.objects
                .filter(author__following__user=self.request.user)
                .select_related("author", "group")
        )


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
