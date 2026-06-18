from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
  path("all_news/", views.get_all_news, name="get_all_news"),
  path("create/", views.create_news, name="create_article"),
  path("<int:id>/", views.get_one_article_user, name="get_article_for_user"),
  path("<int:id>/edit/", views.get_one_article_edit, name="get_article_for_edit"),
  path('<int:id>/delete/', views.delete_news, name='delete_news'),
   path("tags/", views.get_all_tags, name="get_all_tags"),
  path("tags/create/", views.create_tag, name="create_tag"),
]