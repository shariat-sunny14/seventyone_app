from django.urls import path
from . import views

urlpatterns = [
    path('item_consumption_report/', views.consumptionReportManagerAPI, name='item_consumption_report'),
    path('get_item_consumption_details/', views.getconsumptionDetailsAPI, name='get_item_consumption_details'),
    path('get_item_consumption_summary/', views.getconsumptionSummaryAPI, name='get_item_consumption_summary'),
]