from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.checkout, name='checkout'),
    path('confirm/<str:order_number>/', views.order_confirm, name='confirm'),
]
