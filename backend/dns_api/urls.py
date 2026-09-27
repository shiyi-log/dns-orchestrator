from django.urls import path

from . import views


urlpatterns = [
    path("health", views.health),
    path("domains", views.domains),
    path("domains/<str:domain>/records", views.records),
    path("domains/<str:domain>/records/<str:record_id>", views.record_detail),
    path("activity", views.activity),
]
