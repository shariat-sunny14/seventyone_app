from django.urls import path
from . import views

urlpatterns = [
    path('post_order_update_services/', views.postOrderUpdateManageAPI, name='post_order_update_services'),
    path('get_postorder_update_invoice_details/', views.getPostorderUpdateInvoiceDtlsAPI, name='get_postorder_update_invoice_details'),
    path('delete_item_invoicedtl_value/<int:invdtl_id>/', views.deleteItemInvoiceDtlsAPI, name='delete_item_invoicedtl_value'),
    path('update_savepos_bill/', views.updateSavePosBillAPI, name='update_savepos_bill'),
]
