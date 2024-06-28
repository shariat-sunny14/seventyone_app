from django.urls import path
from . import views

urlpatterns = [
    path('user_setup/', views.user_setup, name='user_setup'),
    path('add_user_modal/', views.addUserManageAPI, name='add_user_modal'),
    path('edit_view_user_modal/', views.editUserManageAPI, name='edit_view_user_modal'),
    path('user_password_change/', views.passwordChangeManageAPI, name='user_password_change'),
    path('password_changing_by_user/', views.passwordChangingByUserManageAPI, name='password_changing_by_user'),
    path('user_info_update_by_user/', views.userInfoUpdateByUserManageAPI, name='user_info_update_by_user'),
    path('update_user_password/', views.passwordUpdateManageAPI, name='update_user_password'),
    path('add_user_setup/', views.saveUserAPI, name='add_user_setup'),
    path('update_user_setup/<int:user_id>/', views.updateUserAPI, name='update_user_setup'),
    path('update_userinfo_by_users/<int:user_id>/', views.updateUserInfoByUserManagerAPI, name='update_userinfo_by_users'),
    path('get_branch_options/', views.getBranchOptionsAPI, name='get_branch_options'),
    path('get_org_options/', views.getOrganizationOptionAPI, name='get_org_options'),
    path('get_user_list_values/', views.getUserListsAPI, name='get_user_list_values'),
    path('get_user_wise_store_org_option/', views.getUserWiseOrgOptionAPI, name='get_user_wise_store_org_option'),
    path('get_store_access_org_data/', views.getStoreAccessOrgDataAPI, name='get_store_access_org_data'),
    path('get_orgid_wise_store_value/<int:org_id>/', views.getOrgIdWiseStoreValueAPI, name='get_orgid_wise_store_value'),
    path('save_update_store_access/', views.saveStoreAccessAPI, name='save_update_store_access'),
    # access  
    path('access_manage/', views.useraccessManageAPI, name='access_manage'),
    path('save_user_access/', views.saveAccessAPI, name='save_user_access'),
    # test
    path('testing_access_list/', views.testing_user_access_list, name='testing_access_list'),
]
