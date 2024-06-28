from django.urls import path
from . import views

urlpatterns = [
    path('stock_receive_without_grn_list/', views.without_GRN_listAPI, name='stock_receive_without_grn_list'),
    path('add_receive_stock_withoutgrn/', views.recStockwithout_GRNAPI, name='add_receive_stock_withoutgrn'),
    path('get_rec_stock_without_grn_list/', views.get_recStckwithout_GRNAPI, name='get_rec_stock_without_grn_list'),
    path('get_rec_stock_without_grn_details/', views.get_recStockwithout_grn_details, name='get_rec_stock_without_grn_details'),
    path('edit_receive_stock_withoutgrn/<int:wo_grn_id>/', views.edit_recStockwithout_GRNAPI, name='edit_receive_stock_withoutgrn'),
    path('report_without_grn/<int:wo_grn_id>/', views.reportWithoutGRNAPI, name='report_without_grn'),
    path('stock_receive_WOGRN/', views.receiveStockWogrnAPI, name='stock_receive_WOGRN'),
    path('edit_stock_receive_WOGRN/', views.edit_receiveStockWogrnAPI, name='edit_stock_receive_WOGRN'),
    path('delete_wo_grndtl_value/<int:wo_grndtl_id>/', views.delete_wo_grn, name='delete_wo_grndtl_value'),
    path('exsit_receive_stock_wogrn_data/', views.exsit_receiveStockWogrnAPI, name='exsit_receive_stock_wogrn_data'),
    path('get_wo_grn_list_details/', views.getWGRNListDetailsAPI, name='get_wo_grn_list_details'),
]