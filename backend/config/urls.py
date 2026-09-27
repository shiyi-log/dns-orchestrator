from django.urls import include, path


urlpatterns = [
    path("api/", include("backend.dns_api.urls")),
]
