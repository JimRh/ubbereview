"""brain URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import oauth2_provider.views as oauth2_views

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from brain import settings
from website import views

oauth2_endpoint_views = [
    path('authorize/', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path('token/', oauth2_views.TokenView.as_view(), name='token'),
    path('revoke-token/', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
    path('applications/', oauth2_views.ApplicationList.as_view(), name="list"),
    path('applications/register/', oauth2_views.ApplicationRegistration.as_view(), name="register"),
    re_path(r'^applications/(?P<pk>\d+)/$', oauth2_views.ApplicationDetail.as_view(), name="detail"),
    re_path(r'^applications/(?P<pk>\d+)/delete/$', oauth2_views.ApplicationDelete.as_view(), name="delete"),
    re_path(r'^applications/(?P<pk>\d+)/update/$', oauth2_views.ApplicationUpdate.as_view(), name="update"),
    path('authorized-tokens/', oauth2_views.AuthorizedTokensListView.as_view(), name="authorized-token-list"),
    re_path(r'^authorized-tokens/(?P<pk>\d+)/delete/$', oauth2_views.AuthorizedTokenDeleteView.as_view(), name="authorized-token-delete")
]

schema_view = get_schema_view(
   openapi.Info(
      title="ubbe Api",
      default_version='v3',
      description="## Intro \n"
                  "ubbe (you-bee) is an end-to-end online shipping platform you can use to build, price, and route "
                  "your shipments. ubbe lets you quote, book and track all your shipping needs in one place, making "
                  "the complex world of shipping easy. Use the power of information & speed to make business "
                  "decisions.  With access to real time data, you make informed supply-chain decisions quickly based "
                  "on what matters to you: carrier preference, cost, performance or transit time. It’s like having an "
                  "entire team of logistics professionals working with you. \n"
                  "## Headers \n"
                  "Each api request must include '**ubbe-account**' key in the headers in order to properly configure "
                  "the api requests. The ubbe account number will be given to you along with oauth credentials. \n"
                  "## Responses \n"
                  "All responses returned from ubbe will be in the following standardised format:\n\n"
                  "```{ \"status\": 200, \"is_error\": false, \"errors\": [], \"content\": {}}```",
      terms_of_service="https://www.ubbe.com/terms-of-use",
      contact=openapi.Contact(email="developer@bbex.com"),
      license=openapi.License(name="License"),
   ),
   public=False,
   permission_classes=(permissions.AllowAny,),
)

admin.site.site_title = 'ubbe api'
admin.site.site_header = "ubbe api Administration"
admin.site.index_title = 'ubbe api Administration'

urlpatterns = [
    # url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', login_required(schema_view.with_ui('redoc', cache_timeout=24)), name='schema-redoc'),

path('', views.Login.as_view(), name='Login'),
    path('site-admin/', admin.site.urls),
    path('o/', include((oauth2_endpoint_views, "api"), namespace='oauth2_provider')),

    path('api/v3/', include('api.urls')),
    path('api/v3/books/', include('apps.books.urls')),

    # Fixed Views
    re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon/favicon.ico')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.insert(0, path('__debug__/', include(debug_toolbar.urls))),
