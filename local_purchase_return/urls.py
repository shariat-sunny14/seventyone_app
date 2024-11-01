from django.urls import path
from . import views

urlpatterns = [
    path('local_purchase_return_list/', views.lPReturnListManagerAPI, name='local_purchase_return_list'),
    path('get_local_purchase_return_list/', views.getLocalPurchaseReturnListAPI, name='get_local_purchase_return_list'),
    path('local_purchase_return/<int:lp_id>/', views.localPurchaseReturnManagerAPI, name='local_purchase_return'),
    path('save_local_purchase_returned_service/', views.saveLocalpurchaseReturnedManagerAPI, name='save_local_purchase_returned_service'),
]
