from django.urls import path
from . import views

urlpatterns = [
    path('module_feature_setup/', views.moduleSetupAPI,
         name='module_feature_setup'),
    path('module_manage/', views.moduleManageAPI, name='module_manage'),
    path('add_module/', views.saveModuleAPI, name='add_module'),
    path('delete_module/', views.deleteModuleAPI, name="delete_module"),
    #
    path('module_type_manage/', views.moduleTyteManageAPI,
         name='module_type_manage'),
    path('add_module_type/', views.saveModuleTyteAPI, name='add_module_type'),
    path('delete_type/', views.deleteModuleTypeAPI, name="delete_type"),
    #
    path('feature_manage/', views.moduleFeatureManageAPI, name='feature_manage'),
    path('add_features/', views.saveFeaturesAPI, name='add_features'),
    path('delete_features/', views.deleteFeatureAPI, name="delete_features"),
]
