from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from .views import RegisterView, LogoutView, DashboardView, ProductListView, ProductDetailView, ProductCreateView, ProductEditView, ProductDeleteView, MyPurchasesView, SalesView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:id>/', views.detail, name='detail'),
    path('create-checkout-session/<int:id>/', views.create_checkout_session, name='create_checkout_session'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('success/', views.payment_success_view, name='success'),
    path('failed/', views.payment_failed_view, name='failed'),
    path('createproduct/',views.create_product, name='createproduct'),
    path('editproduct/<int:id>/',views.product_edit, name='editproduct'),
    path('delete/<int:id>/',views.product_delete, name='delete'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('register/',views.register,name='register'),
    path('login/',auth_views.LoginView.as_view(template_name='myapp/login.html'),name='login'),
    path('logout/',auth_views.LogoutView.as_view(),name='logout'),
    path('invalid/',views.invalid,name='invalid'),
    path('purchases/',views.my_purchases,name='purchases'),
    path('sales/',views.sales,name='sales'),
    path("payment-handler/", views.payment_handler, name="payment_handler"),

    path('api/auth/register/', RegisterView.as_view()),
    path('api/auth/login/', TokenObtainPairView.as_view()),
    path('api/auth/refresh/', TokenRefreshView.as_view()),
    path('api/auth/logout/', LogoutView.as_view()),
    path('api/dashboard/', DashboardView.as_view(), name='api_dashboard'),
    path('api/products/', ProductListView.as_view(), name='api_products'),
    path('api/products/<int:id>/', ProductDetailView.as_view(), name='api_product_detail'),
    path('api/products/create/', ProductCreateView.as_view(), name='api_product_create'),
    path('api/products/<int:id>/edit/', ProductEditView.as_view(), name='api_product_edit'),
    path('api/products/<int:id>/delete/', ProductDeleteView.as_view(), name='api_product_delete'),
    path('api/purchases/', MyPurchasesView.as_view(), name='api_purchases'),
    path('api/sales/', SalesView.as_view(), name='api_sales'),
]
