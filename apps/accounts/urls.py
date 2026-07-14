from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import path
app_name = "accounts"
from .forms import SignupForm
def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        return redirect(request.POST.get("next") or "preflight:dashboard")
    return render(request, "registration/signup.html", {"form": form, "next": request.GET.get("next", "")})
urlpatterns = [path("", signup, name="signup")]
