from django.urls import path
from . import views

urlpatterns = [
    path('purchase_order_return_list/', views.POReturnManagerAPI, name='purchase_order_return_list'),
    path('get_purchase_order_return_details/', views.getPurchaseOrderReturnListAPI, name='get_purchase_order_return_details'),
    path('purchase_order_return/<int:po_id>/', views.purchaseOrderReturnAPI, name='purchase_order_return'),
    path('save_purchase_order_return/', views.savePurchaseOrderReturnedAPI, name='save_purchase_order_return'),
    path('purchase_order_returned_report/<int:po_id>/', views.POReturnedReportAPI, name='purchase_order_returned_report'),
]