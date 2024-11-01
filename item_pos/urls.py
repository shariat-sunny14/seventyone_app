from django.urls import path
from . import views

urlpatterns = [
    path('item_pos_billing/', views.item_posAPI, name='pos_billing'),
    path('get_item_list/', views.get_item_listAPI, name='get_item_list'),
    path('select_item_value/', views.select_item_listAPI, name='select_item_value'),
    path('select_item_without_stock_list/', views.selectItemWithoutStocklistAPI, name='select_item_without_stock_list'),
    path('save_pos_billing/', views.save_pos, name='save_pos_billing'),
    path('receipt/', views.receipt, name="receipt_modal"),
    path('search_b2b_clients_for_billing/', views.searchb2bClientsInBillingAPI, name="search_b2b_clients_for_billing"),
    path('select_b2b_clients_details/', views.selectB2bClientsDetailsAPI, name="select_b2b_clients_details"),
    path('rent_others_expense_list/', views.rentOthersExpsManagerAPI, name="rent_others_expense_list"),
    path('get_others_expense_list/', views.getRentOthersExpsListsAPI, name="get_others_expense_list"),
    path('add_carrying_expenses_modal/', views.addExpensesModelManageAPI, name="add_carrying_expenses_modal"),
    path('add_expenses_bill/', views.addExpenseAPI, name="add_expenses_bill"),
    path('save_favorite_item/', views.saveFavoriteItemManagerAPI, name='save_favorite_item'),
    path('get_fav_item_list/', views.getFavItemListManagerAPI, name='get_fav_item_list'),
    path('delete_fav_item/<int:fav_id>/', views.delete_fav_item, name='delete_fav_item'),
    path('add_items_in_pos_billing/', views.itemAddInPosBillingUpdateManagerAPI, name="add_items_in_pos_billing"),
    path('add_items_pos_update_invoice/', views.addItemPosUpdateInvManagerAPI, name="add_items_pos_update_invoice"),
]
