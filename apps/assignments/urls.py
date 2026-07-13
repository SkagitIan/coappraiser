from django.urls import path
from . import views

app_name = "assignments"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("new/", views.assignment_create, name="create"),
    path("<int:pk>/", views.assignment_detail, name="detail"),
]

