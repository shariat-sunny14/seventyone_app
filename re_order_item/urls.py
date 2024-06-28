from django.urls import path
from . import views

urlpatterns = [
    path('re_order_item_list/', views.reOrderItemListAPI, name='re_order_item_list'),
    path('get_re_order_items/', views.getReOrderItemsAPI, name='get_re_order_items'),
]