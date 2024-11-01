from django.urls import path
from . import views

urlpatterns = [
    path('select_bill_receipt_manager/', views.selectBillReceiptManagerAPI, name='select_bill_receipt_manager'),
    path('save_bill_receipt/', views.saveSelectBillReceiptAPI, name='save_bill_receipt'),
    path('get_bill_receipt_options/', views.getReceiptOptionManagerAPI, name='get_bill_receipt_options'),
]