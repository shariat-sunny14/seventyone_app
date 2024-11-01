from django.urls import path
from . import views

urlpatterns = [
    path('customer_registration_services/', views.customerRegistrationManagerAPI, name='customer_registration_services'),
    path('add_registration_modal/', views.addRegistrationModelManageAPI, name="add_registration_modal"),
    path('edit_registration_modal/', views.editRegistrationModelManageAPI, name='edit_registration_modal'),
    path('active_registration/', views.activeRegistrationManagerAPI, name='active_registration'),
    path('active_reg_submission/', views.activeRegSubmissionAPI, name='active_reg_submission'),
    path('inactive_registration/', views.inactiveRegistrationManagerAPI, name='inactive_registration'),
    path('inactive_reg_submission/', views.inactiveRegSubmissionAPI, name='inactive_reg_submission'),
    path('save_update_customer_registrations/', views.saveRegistrationsAPI, name="save_update_customer_registrations"),
    path('get_customer_registration_list/', views.getCustomerRegistrationsListAPI, name="get_customer_registration_list"),
    path('search_registration_for_billing/', views.searchCustomerRegistrationAPI, name="search_registration_for_billing"),
    path('select_registrations_details/', views.selectCustomerRegistrationDtlsAPI, name="select_registrations_details"),
    path('client_summary_registration_reports/<int:reg_id>/', views.regClientSummaryReportsAPI, name="client_summary_registration_reports"),
    path('client_details_registration_reports/<int:reg_id>/', views.regClientsDetailsReportsAPI, name="client_details_registration_reports"),
    path('get_clients_trans_summary_report/', views.getClientsTransactionsSummaryAPI, name="get_clients_trans_summary_report"),
    path('get_clients_trans_details_report/', views.getClientsTransactionsDetailsAPI, name="get_clients_trans_details_report"),
]
