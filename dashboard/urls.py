from django.urls import path
from . import views
from dashboard.views import home

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]