from django.urls import path
from . import views

urlpatterns = [
    path('stock_list_service/', views.stockListManagerAPI, name='stock_list_service'),
    path('get_item_wise_stock/', views.getItemWiseStockAPI, name='get_item_wise_stock'),
    path('item_wise_stock_report/<int:store_id>/', views.stockReportManagerAPI, name='item_wise_stock_report'),
]
