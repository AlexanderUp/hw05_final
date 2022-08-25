from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest


def _get_page_object_from_paginator(
        posts: QuerySet,
        posts_per_page: int,
        request: HttpRequest) -> Page:
    paginator = Paginator(posts, posts_per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
