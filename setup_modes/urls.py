from django.urls import path
from . import views

urlpatterns = [
    path('store_wise_setup_mode/', views.storeWiseSetupModeManagerAPI, name='store_wise_setup_mode'),
    path('get_ui_template/', views.getUITemplateAPI, name='get_ui_template'),
    path('add_update_ui_template/', views.addUpdateUITemplateAPI, name='add_update_ui_template'),
]
