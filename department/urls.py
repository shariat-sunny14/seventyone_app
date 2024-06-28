from django.urls import path
from . import views

urlpatterns = [
    path('departments_list/', views.departmentSetupAPI, name='departments_list'),
    path('get_list_of_departments/', views.get_departments_dataAPI, name='get_list_of_departments'),
    path('get_department_lists/<int:dept_id>/', views.getDepartmentListAPI, name='get_department_lists'),
    path('dept_add_update/', views.department_addupdateAPI, name='dept_add_update'),
]