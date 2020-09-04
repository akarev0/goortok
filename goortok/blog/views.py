from typing import Dict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DeleteView

from .forms import PostCreateForm
from .models import Post, Images


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


@login_required
def post_details(request, pk: int):
    post = get_object_or_404(Post, pk=pk)
    images = Images.objects.filter(post=post)
    context = {
        'post': post,
        'images': images
    }

    return render(request, 'blog/post_detail.html', context=context)


@login_required
def create_post(request):

    ImageFormset = modelformset_factory(Images, fields=('image',), extra=4)

    form = PostCreateForm()
    formset = ImageFormset(queryset=Images.objects.none())

    if request.method == 'POST':
        form = PostCreateForm(request.POST)
        formset = ImageFormset(request.POST or None, request.FILES or None)
        if form.is_valid() and formset.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            for photo in formset:
                try:
                    post_image = Images(post=post, image=photo.cleaned_data['image'])
                    post_image.save()
                except Exception:
                    break
            return redirect('blog-home')

    context: Dict = {
        'form': form,
        'formset': formset
    }

    return render(request, 'blog/post_form.html', context=context)


class PostUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(UserPassesTestMixin, LoginRequiredMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


def about(request):
    return render(request, 'blog/about.html', {'title': 'about'})
