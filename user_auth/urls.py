from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='logger/singin_form.html', redirect_authenticated_user=True), name="login"),
    path('accounts/login/', views.user_loginManagerAPI, name='login'),
    path('user_wise_login/', views.user_loginAPI, name='user_wise_login'),
    path('', views.main_dashboard, name='main_dashboard'),
    path('accounts/profile/', views.main_dashboard, name='main_dashboard'),
    path('user/logout/', views.logoutuser, name='logout'),
    path('fetch_organizations_list/', views.fetch_organizations, name='fetch_organizations_list'),
    path('statistics_dashboard/', views.statisticsManagerAPI, name='statistics_dashboard'),
    path('get_store_wise_stock_qty/', views.storeWiseStockQtyManagerAPI, name='get_store_wise_stock_qty'),
    path('get_total_items_values/', views.get_total_itemsManagerAPI, name='get_total_items_values'),
    path('get_total_consumption_datewise/', views.getConsumptionManagerAPI, name='get_total_consumption_datewise'),
    path('get_total_sales_amt_datewise/', views.getSalesAmountManagerAPI, name='get_total_sales_amt_datewise'),
    path('get_total_collection_amt_datewise/', views.getCollectionAmtManagerAPI, name='get_total_collection_amt_datewise'),
    path('get_details_sales_invoicewise/', views.getDetailsSalesManagerAPI, name='get_details_sales_invoicewise'),
    path('get_item_wise_sales_amt/', views.getItemWiseSalesManagerAPI, name='get_item_wise_sales_amt'),
    path('get_user_org_informations/', views.getUserInfoAPI, name='get_user_org_informations'),

    # 
    path('testlogin', views.testLogin, name='testlogin'),
]
