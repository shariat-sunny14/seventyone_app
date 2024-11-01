from django.urls import path
from . import views

urlpatterns = [
    path('delivery_chalan_services/', views.deliveryChalanManagerAPI, name='delivery_chalan_services'),
    path('manual_delivery_chalan_service/', views.manualDeliveryChalanManagerAPI, name='manual_delivery_chalan_service'),
    path('fetch_delivery_chalan_data/', views.fetchDeliveryChalanDataAPI, name='fetch_delivery_chalan_data'),
    path('update_delivery_chalan/<int:inv_id>/', views.updateDeliveryChalanAPI, name='update_delivery_chalan'),
    path('get_delivery_chalan_data/', views.getDeliveryChalanDataAPI, name='get_delivery_chalan_data'),
    path('save_update_delivery_chalan/', views.saveandUpdateDeliveryChalanAPI, name='save_update_delivery_chalan'),
    path('delivery_chalan/', views.deliveryChalan, name="chalan_modal"),
    path('delivery_chalan_modified_items/', views.deliveryChalanModifiedItems, name="chalan_modal_modified_items"),
    path('delete_chalan_details_items_wise/<int:invdtl_id>/', views.deleteChalanDetailsItemsWiseAPI, name='delete_chalan_details_items_wise'),
]
