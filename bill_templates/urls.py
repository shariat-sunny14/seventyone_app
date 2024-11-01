from django.urls import path
from . import views

urlpatterns = [
    path('bill_template_manager/', views.billTemplateManagerAPI, name='bill_template_manager'),
    path('save_bill_template/', views.saveBillTemplateManagerAPI, name='save_bill_template'),
    path('get_bill_temp_options/', views.getBillTempOptionManagerAPI, name='get_bill_temp_options'),
]