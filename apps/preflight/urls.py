from django.urls import path
from . import views

app_name = "preflight"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("new/", views.create, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/revise/", views.revise, name="revise"),
    path("findings/<int:pk>/decision/", views.decision, name="decision"),
    path("<int:pk>/workfile-record/", views.workfile_record, name="workfile_record"),
    path("<int:pk>/delete/", views.delete_review, name="delete_review"),
    path("files/<int:pk>/download/", views.download_file, name="download_file"),
]
