from django.urls import path
from . import views

urlpatterns = [
    path('sales_report_services/', views.salesReportAPI, name='sales_report_services'),
    path('get_sales_report_values/', views.getSalesReportManagerAPI, name='get_sales_report_values'),
    path('due_reports/', views.dueReportAPI, name='due_reports'),
    path('get_dues_invoice_values/', views.getDueReportManagerAPI, name='get_dues_invoice_values'),
]
