from django.urls import path
from . import views

app_name = "recipes"

urlpatterns = [
    path("s/<int:pk>/", views.short_link_redirect, name="short-link"),
]
