from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="tracker/login.html"
        ),
        name="login"
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout"
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "profile/",
        views.profile_view,
        name="profile"
    ),

    path(
        "predict/",
        views.predict_cycle,
        name="predict"
    ),

    path(
        "period/log/",
        views.log_period,
        name="log_period"
    ),

    path(
        "symptoms/",
        views.symptoms,
        name="symptoms"
    ),

    path(
        "history/",
        views.history,
        name="history"
    ),
]