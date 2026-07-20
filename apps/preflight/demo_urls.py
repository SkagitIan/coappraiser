from django.urls import path

from . import demo_views


app_name = "preflight_demo"

urlpatterns = [
    path("", demo_views.landing, name="landing"),
    path("run/<slug:slug>/", demo_views.start, name="start"),
    path("reviews/<int:pk>/process/", demo_views.process, name="process"),
    path("reviews/<int:pk>/stream/", demo_views.stream, name="stream"),
    path("reviews/<int:pk>/", demo_views.detail, name="detail"),
    path("reviews/<int:pk>/retry/", demo_views.retry, name="retry"),
    path("reviews/<int:pk>/workfile/", demo_views.workfile, name="workfile"),
    path("reviews/<int:pk>/workfile.json", demo_views.workfile_download, name="workfile_download"),
    path("findings/<int:pk>/decision/", demo_views.decision, name="decision"),
    path("files/<int:pk>/download/", demo_views.download_file, name="download_file"),
]
