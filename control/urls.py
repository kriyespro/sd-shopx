from django.urls import path
from . import views

app_name = 'control'

urlpatterns = [
    path('login/', views.ControlLoginView.as_view(), name='login'),
    path('logout/', views.control_logout_get, name='logout'),

    path('', views.DashboardView.as_view(), name='dashboard'),
    path('stats/', views.StatsCardView.as_view(), name='stats'),
    path('activity/', views.ActivityFeedView.as_view(), name='activity'),

    # Staff users (superuser only)
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/ban/', views.ban_user, name='ban_user'),
    path('users/<int:pk>/unban/', views.unban_user, name='unban_user'),
    path('users/<int:pk>/role/', views.assign_role, name='assign_role'),
    path('users/<int:pk>/impersonate/', views.impersonate_user, name='impersonate_user'),
    path('stop-impersonate/', views.stop_impersonate, name='stop_impersonate'),

    # Customers (buyers)
    path('customers/', views.CustomerListView.as_view(), name='customers'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),

    # Products
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/new/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductEditView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.delete_product, name='product_delete'),
    path('products/<int:pk>/toggle/', views.toggle_product_status, name='product_toggle'),
    path('products/<int:pk>/images/', views.ProductImageUploadView.as_view(), name='product_image_upload'),
    path('products/images/<int:pk>/delete/', views.delete_product_image, name='product_image_delete'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.delete_category, name='category_delete'),

    # Orders
    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:order_pk>/payment/', views.PaymentSaveView.as_view(), name='payment_save'),
    path('orders/<int:order_pk>/refund/', views.RefundCreateView.as_view(), name='refund_create'),

    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payments'),

    # Refunds
    path('refunds/', views.RefundListView.as_view(), name='refunds'),
    path('refunds/<int:pk>/', views.RefundDetailView.as_view(), name='refund_detail'),

    # Inventory
    path('inventory/', views.InventoryView.as_view(), name='inventory'),

    # Reviews
    path('reviews/', views.ReviewListView.as_view(), name='reviews'),
    path('reviews/<int:pk>/toggle/', views.toggle_review, name='review_toggle'),
    path('reviews/<int:pk>/delete/', views.delete_review, name='review_delete'),
]
