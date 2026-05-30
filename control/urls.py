from django.urls import path
from . import views

app_name = 'control'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('stats/', views.StatsCardView.as_view(), name='stats'),
    path('activity/', views.ActivityFeedView.as_view(), name='activity'),

    path('users/', views.UserListView.as_view(), name='users'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/ban/', views.ban_user, name='ban_user'),
    path('users/<int:pk>/unban/', views.unban_user, name='unban_user'),

    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/new/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductEditView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.delete_product, name='product_delete'),
    path('products/<int:pk>/images/', views.ProductImageUploadView.as_view(), name='product_image_upload'),
    path('products/images/<int:pk>/delete/', views.delete_product_image, name='product_image_delete'),

    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.delete_category, name='category_delete'),

    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
]
