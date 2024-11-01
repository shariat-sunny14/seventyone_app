from django.urls import path
from . import views

urlpatterns = [
    path('banks_setup_manager/', views.bankSetupManagerAPI, name='banks_setup_manager'),
    path('add_banks_setup_modal/', views.addBankSetupManageAPI, name='add_banks_setup_modal'),
    path('add_update_banks/', views.addUpdateBankSetupAPI, name='add_update_banks'),
    path('get_banks_options/', views.getBankSetupOptionsAPI, name='get_banks_options'),
    path('get_banks_list/', views.getBankSetupListsAPI, name='get_banks_list'),
    path('edit_banks_setup/', views.editBankSetupManageAPI, name='edit_banks_setup'),
]
