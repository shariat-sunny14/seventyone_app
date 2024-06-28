from django.urls import path
from . import views

urlpatterns = [
    path('invoice_list/', views.invoice_listAPI, name='invoice_list'),
    path('get_Invoice_list/', views.get_Invoice_listAPI, name='get_Invoice_list'),
    path('testing_invoice/', views.testingInvoiceListAPI, name='testing_invoice'),
]