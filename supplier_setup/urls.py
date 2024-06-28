from django.urls import path
from . import views

urlpatterns = [
    path('supplier_manufacturer_setup/', views.supplierManufecAPI, name='supplier_manufacturer_setup'),
    path('list_of_supplier/', views.get_supplier_dataAPI, name='list_of_supplier'),
    path('get_supplier_lists/<int:supplier_id>/', views.getSupplierListAPI, name='get_supplier_lists'),
    path('supplier_add_update/', views.supplier_addupdateAPI, name='supplier_add_update'),
    # 
    path('list_of_menufecturer/', views.get_menufec_dataAPI, name='list_of_menufecturer'),
    path('get_menufecture_lists/<int:manufac_id>/', views.getMenufecturerListAPI, name='get_menufecture_lists'),
    path('menufecture_add_update/', views.menufecture_addupdateAPI, name='menufecture_add_update'),
]
