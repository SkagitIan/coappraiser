from django.urls import path
from .views import detail, update_verification
app_name = "workfile"
urlpatterns = [path("<int:pk>/", detail, name="detail"), path("verification/<int:pk>/update/", update_verification, name="update_verification")]
