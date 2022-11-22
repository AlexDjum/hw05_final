from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginator

POST_COUNT: int = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = paginator(posts, request, POST_COUNT)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()  # type: ignore
    page_obj = paginator(posts, request, POST_COUNT)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()  # type: ignore
    count = author.posts.count()  # type: ignore
    page_obj = paginator(posts, request, POST_COUNT)
    follow = Follow.objects.filter(author=author)
    following = follow.exists() and request.user.is_authenticated
    context = {
        'page_obj': page_obj,
        'count': count,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    count_posts = post.author.posts.all().count()  # type: ignore
    comments = post.comments.all()  # type: ignore
    context = {
        'post': post,
        'count': count_posts,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user)
    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect("posts:post_detail", post_id)
    return render(request, "posts/create_post.html", {"form": form,
                                                      "post": post,
                                                      "is_edit": True})


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.delete()
    return redirect('posts:profile', request.user)


@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user)
    posts = Post.objects.filter(author__following__user=user).all()
    page_obj = paginator(posts, request, POST_COUNT)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author).exists()
    if not follow and username != request.user.username:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    query = Follow.objects.filter(user=request.user, author=author)
    follow = query.exists()
    if follow:
        query.delete()
    return redirect('posts:follow_index')
