from django.urls import path
from . import views

urlpatterns = [
    path('purchase_order_list/', views.purchaseOrderManagerAPI, name='purchase_order_list'),
    path('add_purchase_order/', views.managePurchaseOrderAPI, name='add_purchase_order'),
    path('get_purchage_order_entry_list/', views.getPOEntrylistAPI, name='get_purchage_order_entry_list'),
    path('select_po_entrylist_details/', views.selectPOEntryListDetailsAPI, name='select_po_entrylist_details'),
    path('get_user_stores/', views.get_user_stores, name='get_user_stores'),
    path('get_po_re_order_item_list/', views.getPOReOrderItemListAPI, name='get_po_re_order_item_list'),
    path('add_purchase_order_generate/', views.addPurchaseOrderGenerateAPI, name='add_purchase_order_generate'),
    path('get_purchase_order_list/', views.getPurchaseOrderListAPI, name='get_purchase_order_list'),
    path('update_purchase_order/<int:po_id>/', views.updatePurchaseOrderAPI, name='update_purchase_order'),
    path('purchase_order_proposal_report/<int:po_id>/', views.purchaseOrderProposalReportAPI, name='purchase_order_proposal_report'),
    path('edit_update_purchase_order/', views.editUpdatePOManagerAPI, name='edit_update_purchase_order'),
    path('delete_po_details_items/<int:podtl_id>/', views.deletePurchaseOrderdtlsItemAPI, name='delete_po_details_items'),
]