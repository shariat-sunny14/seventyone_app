from django.urls import path
from . import views

urlpatterns = [
    path('local_purchase_list_service/', views.localPurchaselistManagerAPI, name='local_purchase_list_service'),
    path('local_purchase_approval_list/', views.localPurchaseApprovallistAPI, name='local_purchase_approval_list'),
    path('get_local_purchase_list/', views.getLocalPurchaseListAPI, name='get_local_purchase_list'),
    path('receive_stock_local_purchase/', views.receiveStockLocalPurchaseManagerAPI, name='receive_stock_local_purchase'),
    path('save_receive_local_purchase/', views.receiveLocalPurchaseStockAPI, name='save_receive_local_purchase'),
    path('edit_update_local_purchase/<int:lp_id>/', views.editUpdateLocalPurchaseManagerAPI, name='edit_update_local_purchase'),
    path('approval_local_purchase/<int:lp_id>/', views.approvalLocalPurchaseManagerAPI, name='approval_local_purchase'),
    path('edit_update_save_local_purchase/', views.updateLocalPurchaseManagerAPI, name='edit_update_save_local_purchase'),
    path('delete_local_purchase_details/<int:lp_dtl_id>/', views.deleteLocalPurchaseDetails, name='delete_local_purchase_details'),
    path('local_purchase_report/<int:lp_id>/', views.localPurchaseReportManagerAPI, name='local_purchase_report'),
    path('local_purchase_details_reports/', views.localPurchaseDetailsReportsAPI, name="local_purchase_details_reports"),
    path('lp_org_wise_details_reports/', views.lpOrgWiseDetailsReportsAPI, name='lp_org_wise_details_reports'),
]
