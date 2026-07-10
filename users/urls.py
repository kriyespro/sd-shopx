from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_edit, name='profile'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('wishlist/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
]
