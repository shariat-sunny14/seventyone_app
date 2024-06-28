from django.urls import path
from . import views

urlpatterns = [
    path('credit_service_list/', views.creditManagementAPI, name='credit_service_list'),
    path('credit_report_services/', views.reportCreditManagerAPI, name='credit_report_modal'),
    path('list_of_clients/', views.getClientsListAPI, name='list_of_clients'),
    path('add_credit_transaction/', views.addCreditTransactionAPI, name='add_credit_transaction'),
    path('get_credit_transactions/', views.getCreditTransactionsAPI, name='get_credit_transactions'),
]