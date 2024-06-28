from django.urls import path
from . import views

urlpatterns = [
    path('store_setup/', views.store_setupAPI, name='store_setup'),
    path('load_template/', views.load_templateAPI, name='load_template'),
    path('get_store_lists/<int:store_id>/', views.getStoreListAPI, name='get_store_lists'),
    # branch wise store
    path('get_list_of_store/', views.get_store_dataAPI, name='get_list_of_store'),
    path('branch_store_add_update/', views.store_addupdateAPI, name='branch_store_add_update'),
    # org wise store
    path('get_list_of_org_store/', views.getOrgStoreDataAPI, name='get_list_of_org_store'),
    path('org_store_add_update/', views.orgStoreAddUpdateAPI, name='org_store_add_update'),
]