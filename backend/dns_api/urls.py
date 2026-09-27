from django.urls import path

from . import views


urlpatterns = [
    path("health", views.health),
    path("domains", views.domains),
    path("domains/<str:domain>/records", views.records),
    path("domains/<str:domain>/records/<str:record_id>", views.record_detail),
    path("activity", views.activity),
    path("providers", views.providers),
    path("accounts", views.accounts),
    path("accounts/<str:account_id>", views.account_detail),
    path("accounts/<str:account_id>/verify", views.verify_account),
    path("accounts/<str:account_id>/set-default", views.set_default_account),
    path("accounts/<str:account_id>/zones", views.account_zones),
    path("accounts/<str:account_id>/zones/<str:zone>/records", views.account_records),
    path("accounts/<str:account_id>/zones/<str:zone>/records/<str:record_id>", views.account_record_detail),
]
