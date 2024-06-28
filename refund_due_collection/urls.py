from django.urls import path
from . import views

urlpatterns = [
    path('due_refund_cancel_services/', views.dueRefundManageAPI, name='due_refund_cancel_services'),
    path('item_wise_invoice_cancel_details/<int:inv_id>/', views.getInvoiceDataAPI, name='item_wise_invoice_cancel_details'),
    path('update_item_wise_invoice_details/', views.updateInvoiceCancelAPI, name='update_item_wise_invoice_details'),
    path('due_refund_details_view/<int:inv_id>/', views.getDueRefundDataAPI, name='due_refund_details_view'),
    path('refund_amount_details_view/<int:inv_id>/', views.getRefundAmountDataAPI, name='refund_amount_details_view'),
    path('save_due_ollection_amount/', views.saveDueCollectionAmountAPI, name='save_due_ollection_amount'),
    path('save_refund_amount/', views.saveRefundAmountAPI, name='save_refund_amount'),
    path('invoice_cancel_details/<int:inv_id>/', views.invoiceCancelDetailsAPI, name='invoice_cancel_details'),
    path('allcancel_invoice_details/', views.invoiceCancelAPI, name='allcancel_invoice_details'),
]