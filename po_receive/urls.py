from django.urls import path
from . import views

urlpatterns = [
    path('purchase_order_receive_list/', views.POReceiveManagerAPI, name='purchase_order_receive_list'),
    path('get_po_receive_details/', views.getPurchaseOrderReceivedListAPI, name='get_po_receive_details'),
    path('po_receive_details_list/<int:po_id>/', views.POReceivedItemDetailsListAPI, name='po_receive_details_list'),
    path('received_purchase_order_details/', views.recievedPODetailsListAPI, name='received_purchase_order_details'),
    path('purchase_order_receive_report/<int:po_id>/', views.POReceivedReportAPI, name='purchase_order_receive_report'),
    path('purchase_order_list_viewers/', views.openPurchaseOrderListModalManageAPI, name='purchase_order_list_viewers'),
]