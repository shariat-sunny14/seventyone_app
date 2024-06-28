from django.urls import path
from . import views

urlpatterns = [
    path('organizations_list/', views.organizationSetupAPI, name='organizations_list'),
    path('get_list_of_organization/', views.get_organization_dataAPI, name='get_list_of_organization'),
    path('get_organization_lists/<int:org_id>/', views.getOrganizationListAPI, name='get_organization_lists'),
    path('org_add_update/', views.organization_addupdateAPI, name='org_add_update'),
    # 
    path('get_list_of_branchs/', views.getBranchsDataAPI, name='get_list_of_branchs'),
    path('select_branch_lists/<int:branch_id>/', views.selectBranchListAPI, name='select_branch_lists'),
    path('branch_add_update/', views.branchAddUpdateAPI, name='branch_add_update'),
]