from django.urls import path
from . import views
from .views import (
    EmployeeLoginView,
    AdminLoginView,
    admin_dashboard,
    edit_employee,
    delete_employee,
    get_employee,
    landing_page,
    employee_dashboard,
    custom_logout,
    add_employee,
    request_demo,
    demo_page,
    predict_view,
    create_facebook_post
)

urlpatterns = [
    path('login/', EmployeeLoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),

    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),

    path('admin/employees/get/<int:employee_id>/', get_employee, name='get_employee'),
    path('admin/employees/add/', add_employee, name='add_employee'),
    path('admin/employees/edit/<int:employee_id>/', edit_employee, name='edit_employee'),
    path('admin/employees/delete/<int:employee_id>/', delete_employee, name='delete_employee'),

    path('dashboard/', employee_dashboard, name='employee_dashboard'),
    path('landing/', landing_page, name='landing_page'),
    path('home/', landing_page, name='home'),
    path('request-demo/', request_demo, name='request_demo'),

    
    path('Demo/', demo_page, name='demo_page'),
    path('predict/', predict_view, name='predict_view'),
    
    # Nouvelle URL pour créer un post Facebook
    path('create-facebook-post/', create_facebook_post, name='create_facebook_post'),

    path('linkedin/etape1/', views.etape1_linkedin, name='etape1_linkedin'),
    path('linkedin/etape2/', views.etape2_linkedin, name='etape2_linkedin'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update-profile-image/', views.update_profile_image, name='update_profile_image'),

]