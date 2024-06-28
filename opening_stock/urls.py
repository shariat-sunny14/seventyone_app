from django.urls import path
from . import views

urlpatterns = [
    path('opening_stock/', views.opening_stockAPI, name='opening_stock'),
    path('add_opening_stock_service/', views.manage_Opening_StockAPI, name='add_opening_stock_service'),
    path('get_opening_stock_list_details/', views.getOpeningStockListDetailsAPI, name='get_opening_stock_list_details'),
    path('get_opening_stock_list/', views.get_Opening_Stock_listAPI, name='get_opening_stock_list'),
    path('get_os_item_details_list/', views.get_OSItem_details, name='get_os_item_details_list'),
    path('add_opening_stock/', views.Addopening_stock, name='add_opening_stock'),
    path('edit_opening_stock/<int:op_st_id>/', views.edit_opening_stockAPI, name='edit_opening_stock'),
    path('report_opening_stock/<int:op_st_id>/', views.reportOpeningStockAPI, name='report_opening_stock'),
    path('edit_update_opening_stock/', views.editUpdate_openingStockAPI, name='edit_update_opening_stock'),
    path('delete_ops_dtls_value/<int:op_stdtl_id>/', views.delete_ops_dtls, name='delete_ops_dtls_value'),
    path('exists_opningStock_data/', views.exist_openingstockAPI, name='exists_opningStock_data'),
]