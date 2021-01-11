from django.core import paginator
from django.core.checks import messages
from django.db import connection
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from django.db.models import Count
from django.contrib.postgres.search import SearchRank, \
    SearchVector, SearchQuery, TrigramSimilarity

from taggit.models import Tag

from .models import Comment, Post
from .forms import EmailPostForm, CommentForm, SearchForm
from mysite.settings import FROM_EMAIL

# Create your views here.
def post_list(request, tag_slug=None):
    object_list = Post.objects.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 5)
    page = request.GET.get('page')
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # if page is not an integer show the first page
        posts = paginator.page(1)
    except EmptyPage:
        # if page is out of range show last page of the results
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'posts':posts, 
                                                   'tag':tag})

# class PostListView(ListView):
#     # queryset = Post.objects.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'
#     tag = None


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                            publish__year=year,
                            publish__month=month,
                            publish__day=day)

    #list of all active comment for this post 
    comments = post.comments.filter(active=True)
    form = CommentForm()
    new_comment = None

    post_tag_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tag_ids).exclude(id=post.id)
    similar_posts = similar_posts.aggregate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.user = request.user
            new_comment.post = post
            new_comment.save()

    return render(request,'blog/post/detail.html', {'post':post, 
                                                    'comments':comments,
                                                    'comment_form':form,
                                                    'new_comment':new_comment,
                                                    'similar_posts':similar_posts})


def post_share(request, post_id):
    # retrive post by ID
    post = get_object_or_404(Post, id=post_id, status='published')
    form = EmailPostForm()
    sent=False

    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{data['name']} reccomends you read {post.title}"
            message = f"Read {post.title} at {post_url} \n\n"\
                      f"{data['name']}'s comment: {data['comment']}"
            send_mail(subject, message, FROM_EMAIL, [data['email_to']])
            sent=True
    return render(request, 'blog/post/share.html', {'post':post, 
                                                'form':form, 'sent':sent})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            #search_vector = SearchVector('title', 'body')
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            # results = Post.published.annotate(rank=SearchRank(search_vector,
            # search_query)).filter(rank__gte=0.3).order_by('-rank')
            results = Post.published.annotate(similarity=TrigramSimilarity('title',
            'query')).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request, 'blog/post/search.html', {
        'form':form, 'query':query, 'results':results
    })