from django.urls import path
from . import views

urlpatterns = [
    path('item_wise_barcode_services/', views.itemBarcodeManagerAPI, name='item_wise_barcode_services'),
    path('get_item_wise_barcode/', views.getItemWiseBarcodeAPI, name='get_item_wise_barcode'),
    path('generate_item_wise_barcode/', views.generate_barcode, name='generate_item_wise_barcode'),
    path('get_barcode_updated_status/<int:stock_id>/', views.get_barcode_status, name='get_barcode_updated_status'),
    path('generate_all_barcode/', views.generate_barcode_bulk, name='generate_all_barcode'),
    
    
    # path('print_item_barcode/', views.print_barcode, name='print_item_barcode'),
]