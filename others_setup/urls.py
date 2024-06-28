from django.urls import path
from . import views

urlpatterns = [
    path('type_uom_category/', views.TypeUomCategoryAPI, name='type_uom_category'),
    # type
    path('get_list_of_type/', views.get_type_dataAPI, name='get_list_of_type'),
    path('get_type_lists/<int:type_id>/', views.getTypeListAPI, name='get_type_lists'),
    path('type_add_update/', views.type_addupdateAPI, name='type_add_update'),
    # uom
    path('get_list_of_uom/', views.get_uom_dataAPI, name='get_list_of_uom'),
    path('get_uom_lists/<int:item_uom_id>/', views.getUoMListAPI, name='get_uom_lists'),
    path('uom_add_update/', views.uom_addupdateAPI, name='uom_add_update'),
    # category
    path('get_list_of_category/', views.get_category_dataAPI, name='get_list_of_category'),
    path('get_category_lists/<int:category_id>/', views.getCategoryListAPI, name='get_category_lists'),
    path('category_add_update/', views.category_addupdateAPI, name='category_add_update'),
]
