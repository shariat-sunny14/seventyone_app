from django.urls import path
from . import views

urlpatterns = [
    path('drivers_setup_manager/', views.driversSetupManagerAPI, name='drivers_setup_manager'),
    path('add_drivers_setup_modal/', views.addDriversManageAPI, name='add_drivers_setup_modal'),
    path('add_update_drivers/', views.addUpdateDriversAPI, name='add_update_drivers'),
    path('get_drivers_options/', views.getDriversOptionsAPI, name='get_drivers_options'),
    path('get_drivers_list/', views.getDriversListsAPI, name='get_drivers_list'),
    path('edit_drivers_setup/', views.editDriverSetupManageAPI, name='edit_drivers_setup'),
]
