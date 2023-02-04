from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from .models import Post, Group, User
from .utils import get_context_page

COUNT_POST_PAGE = 10
TEXT_SHORT = 30


def index(request):
    posts = Post.objects.all()
    page_obj = get_context_page(request, posts, COUNT_POST_PAGE)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_context_page(request, group.posts.all(), COUNT_POST_PAGE)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_total_posts = author.posts.all()
    page_obj = get_context_page(request, author_total_posts, COUNT_POST_PAGE)
    context = {
        'author': author,
        'author_total_posts': author_total_posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author_total_posts = post.author.posts.all()
    title = 'Пост: ' + post.text[:TEXT_SHORT]
    context = {
        'post': post,
        'author_total_posts': author_total_posts,
        'title': title,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect(reverse('posts:profile',
                            kwargs={'username': request.user}))


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if post.author != request.user:
        return redirect(reverse('posts:profile',
                                kwargs={'username': request.user}))
    if form.is_valid():
        post = form.save()
        return redirect(reverse('posts:post_detail',
                        kwargs={'post_id': post_id}))
    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': is_edit, 'post': post})
