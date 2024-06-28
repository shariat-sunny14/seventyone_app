from django.urls import path
from . import views

urlpatterns = [
    path('business_to_business_percentage/', views.b2bClientsManagementAPI, name='business_to_business_percentage'),
    path('business_to_business_rate_setup/', views.b2bCRateSetupManagementAPI, name='business_to_business_rate_setup'),
    path('get_org_wise_item_data/', views.getOrgWiseFilterateItemsAPI, name='get_org_wise_item_data'),
    path('get_list_of_client_item_data/', views.getListOfClientsItemRateAPI, name='get_list_of_client_item_data'),
    path('get_org_wise_dept_data/', views.getOrgWiseFilterateDeptsAPI, name='get_org_wise_dept_data'),
    path('save_update_b2b_client_item_rate/', views.saveUpdateB2bClientItemRateAPI, name='save_update_b2b_client_item_rate'),
    path('get_b2b_client_item_rate/<int:item_id>/', views.getItemListWiseB2bClientItemRateAPI, name='get_b2b_client_item_rate'),
    path('add_update_b2b_item_percentage/', views.addUpdateB2bDeptItemPercentageAPI, name='add_update_b2b_item_percentage'),
    path('get_items_percentage_amt/', views.fetchItemsPercentageAmtAPI, name='get_items_percentage_amt'),
    path('get_depts_percentage_amt/', views.fetchDeptsPercentageAmtAPI, name='get_depts_percentage_amt'),
    path('get_b2b_clients_list/', views.getB2bClientsListManagerAPI, name='get_b2b_clients_list'),
]