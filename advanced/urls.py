from django.urls import path
from . import views

app_name = 'advanced'

urlpatterns = [
    # Vendor URLs
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('vendors/<int:pk>/update/', views.vendor_update, name='vendor_update'),
    path('vendors/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),
    path('vendors/<int:pk>/contacts/', views.vendor_contacts, name='vendor_contacts'),
    path('vendors/<int:pk>/contracts/', views.vendor_contracts, name='vendor_contracts'),
    
    # Contract URLs
    path('contracts/', views.contract_list, name='contract_list'),
    path('contracts/create/', views.contract_create, name='contract_create'),
    path('contracts/<int:pk>/', views.contract_detail, name='contract_detail'),
    path('contracts/<int:pk>/update/', views.contract_update, name='contract_update'),
    path('contracts/<int:pk>/delete/', views.contract_delete, name='contract_delete'),
    path('contracts/<int:pk>/payments/', views.contract_payments, name='contract_payments'),
    
    # Team URLs
    path('team/', views.team_list, name='team_list'),
    path('team/create/', views.team_member_create, name='team_member_create'),
    path('team/<int:pk>/update/', views.team_member_update, name='team_member_update'),
    path('team/<int:pk>/delete/', views.team_member_delete, name='team_member_delete'),
    
    # Task URLs
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/update/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/comment/', views.task_add_comment, name='task_add_comment'),
    path('tasks/export/', views.task_export, name='task_export'),
    path('tasks/bulk-update/', views.task_bulk_update, name='task_bulk_update'),

    # Privacy URLs
    path('privacy/', views.privacy_settings, name='privacy_settings'),
    path('privacy/export/', views.data_export_request, name='data_export_request'),
    path('privacy/export/<int:pk>/', views.data_export_download, name='data_export_download'),
    
    # Usher Assignment URLs
    path('ushers/', views.usher_list, name='usher_list'),
    path('ushers/create/', views.usher_create, name='usher_create'),
    path('ushers/<int:pk>/update/', views.usher_update, name='usher_update'),
    path('ushers/<int:pk>/delete/', views.usher_delete, name='usher_delete'),
]