from django.urls import path
from . import views

urlpatterns = [
    path('po_return_receive_list/', views.POReturnReceiveManagerAPI, name='po_return_receive_list'),
    path('get_po_return_receive_details/', views.getPOReturnReceiveListAPI, name='get_po_return_receive_details'),
    path('purchase_order_return_receive/<int:po_id>/', views.purchaseOrderReturnReceivedAPI, name='purchase_order_return_receive'),
    path('save_purchase_order_return_receive/', views.savePOReturnReceivedAPI, name='save_purchase_order_return_receive'),
    path('po_return_receive_report/<int:po_id>/', views.POReturnReceivedReportAPI, name='po_return_receive_report'),
]