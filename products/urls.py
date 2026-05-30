from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.shop, name='shop'),
    path('search/', views.search, name='search'),
    path('collection/<slug:slug>/', views.collection, name='collection'),
    path('<slug:slug>/', views.product_detail, name='detail'),
]
