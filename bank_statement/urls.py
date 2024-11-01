from django.urls import path
from . import views

urlpatterns = [
    path('bank_statement_list/', views.bankStatementManagerAPI, name="bank_statement_list"),
    path('deposit_in_branch_statement_list/', views.depositInbranchStatementAPI, name="deposit_in_branch_statement_list"),
    path('deposit_rec_in_branch_statement_list/', views.depositReceivedInbranchStatementAPI, name="deposit_rec_in_branch_statement_list"),
    path('get_bank_statement_list/', views.getBankStatementListsAPI, name="get_bank_statement_list"),
    path('get_deposit_in_branch_lists/', views.getDepositInBranchListsAPI, name="get_deposit_in_branch_lists"),
    path('get_deposit_received_sub_branch_lists/', views.getDepRecAtSubBranchListAPI, name="get_deposit_received_sub_branch_lists"),
    path('add_bank_statement_modal/', views.addBankStatementModelManageAPI, name="add_bank_statement_modal"),
    path('add_deposit_main_branch_model/', views.addDepositAtMainBranchModelAPI, name="add_deposit_main_branch_model"),
    path('add_dep_received_sub_branch_model/', views.addDepReceivedAtSubBranchModelAPI, name="add_dep_received_sub_branch_model"),
    path('add_bank_statement_deposit/', views.addBankStatementAPI, name="add_bank_statement_deposit"),
    path('save_deposit_main_branch/', views.saveDepositAtMainBranchStatementAPI, name="save_deposit_main_branch"),
    path('save_receive_deposit_main_branch/', views.saveReceivedDepositAtmainBranchAPI, name="save_receive_deposit_main_branch"),
]
