from django.urls import path
from . import views

urlpatterns = [
    path('stock_reconciliation_service/', views.stockReconciliationManagerAPI, name='stock_reconciliation_service'),
    path('get_reconciliation_items/', views.getReconciliationItemListAPI, name='get_reconciliation_items'),
    path('select_Reconciliation_value/', views.selectReconciliationItemAPI, name='select_Reconciliation_value'),
    path('save_reconciliation/', views.saveReconsalationManagerAPI, name='save_reconciliation'),
    path('get_reconciliation_list/', views.getReconciliationItemAPI, name='get_reconciliation_list'),
    path('show_reconciliation_details/', views.showReconciliationItemDetailsAPI, name='show_reconciliation_details'),
    path('delete_recon_dtl_value/<int:recondtl_id>/', views.deleteReconciliationDtls, name='delete_recon_dtl_value'),
]
