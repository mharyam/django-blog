from django.contrib import admin
from .models import Post, Comment

# Register your models here.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'author', 'publish', 'status')
    list_filter = ('status', 'created', 'publish', 'author')
    search_fields = ('title', )
    raw_id_fields = ('author', )
    date_hierarchy = 'publish'
    ordering = ('status', 'publish')
    popup_response_template = {'slug': ('title',)} #{'slug':('title', )}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
 list_display = ('post', 'created', 'active', 'user')
 list_filter = ('active', 'created', 'updated')
 search_fields = ('body',)