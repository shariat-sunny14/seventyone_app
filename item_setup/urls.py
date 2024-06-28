from django.urls import path
from . import views

urlpatterns = [
    path('item_setup/', views.item_setupAPI, name='item_setup'),
    path('item_add/', views.item_addAPI, name='item_add'),
    path('get_item_lists/<int:item_id>/', views.getItemListAPI, name='get_item_lists'),
    path('delete_supplier_value/<int:supplierdtl_id>/', views.deleteSupplierAPI, name='delete_supplier_value'),
    path('list_of_item/', views.get_items, name='list_of_item'),
    path('get_list_of_item_type/', views.getItemTypeListAPI, name='get_list_of_item_type'),
    path('get_list_of_item_uom/', views.getItemUoMListAPI, name='get_list_of_item_uom'),
    path('get_list_of_item_category/', views.getItemCategoryListAPI, name='get_list_of_item_category'),
    path('get_list_of_manufacturer/', views.getManufacturerListAPI, name='get_list_of_manufacturer'),
    path('get_list_of_supplier/', views.getSupplierListAPI, name='get_list_of_supplier'),
    # test
    path('testing/', views.demoApi, name='testing'),
]