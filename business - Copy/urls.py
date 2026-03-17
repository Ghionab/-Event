from django.urls import path
from . import views

app_name = 'business'

urlpatterns = [
    # Sponsor Management
    path('sponsors/', views.sponsor_list, name='sponsor_list'),
    path('sponsors/create/', views.sponsor_create, name='sponsor_create'),
    path('sponsors/<int:sponsor_id>/', views.sponsor_detail, name='sponsor_detail'),
    path('sponsors/<int:sponsor_id>/edit/', views.sponsor_edit, name='sponsor_edit'),
    path('sponsors/<int:sponsor_id>/delete/', views.sponsor_delete, name='sponsor_delete'),
    path('sponsors/<int:sponsor_id>/materials/', views.sponsor_materials, name='sponsor_materials'),
    path('sponsors/<int:sponsor_id>/leads/', views.sponsor_leads, name='sponsor_leads'),
    path('sponsors/<int:sponsor_id>/leads/import/', views.import_leads, name='import_leads'),
    
    # Analytics
    path('analytics/', views.analytics_overview, name='analytics_overview'),
    path('analytics/event/<int:event_id>/', views.event_analytics, name='event_analytics'),
    path('analytics/event/<int:event_id>/export/', views.export_analytics, name='export_analytics'),
    
    # Financial Tools - Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:expense_id>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:expense_id>/delete/', views.expense_delete, name='expense_delete'),
    
    # Financial Tools - Budget
    path('budget/', views.budget_list, name='budget_list'),
    path('budget/create/', views.budget_create, name='budget_create'),
    path('budget/<int:budget_id>/edit/', views.budget_edit, name='budget_edit'),
    
    # Financial Tools - Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:invoice_id>/send/', views.invoice_send, name='invoice_send'),
    path('invoices/<int:invoice_id>/mark-paid/', views.invoice_mark_paid, name='invoice_mark_paid'),
    
    # Financial Tools - Quotes
    path('quotes/', views.quote_list, name='quote_list'),
    path('quotes/create/', views.quote_create, name='quote_create'),
    path('quotes/<int:quote_id>/', views.quote_detail, name='quote_detail'),
    path('quotes/<int:quote_id>/edit/', views.quote_edit, name='quote_edit'),
    path('quotes/<int:quote_id>/convert/', views.quote_convert, name='quote_convert'),
    
    # Reports
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<int:report_id>/generate/', views.report_generate, name='report_generate'),
    path('reports/<int:report_id>/export/', views.report_export, name='report_export'),
    
    # Dashboard
    path('dashboard/', views.business_dashboard, name='business_dashboard'),
]