from django.urls import path
from . import views

urlpatterns = [
    path('manual_return_receive_service/', views.manualReturnRecriveManagerAPI, name='manual_return_receive_service'),
    path('get_manual_return_list/', views.getManualReturnListAPI, name='get_manual_return_list'),
    path('receive_new_manual_return/', views.ReceiveNewManualReturnAPI, name='receive_new_manual_return'),
    path('save_receive_manual_return_stock/', views.receiveManualReturnStockAPI, name='save_receive_manual_return_stock'),
    path('edit_pdate_receive_manual_return/<int:manu_ret_rec_id>/', views.editUpdateReceiveManualReturnAPI, name='edit_pdate_receive_manual_return'),
    path('save_edit_update_receive_manual_return/', views.updateReceiveManualReturnAPI, name='save_edit_update_receive_manual_return'),
    path('delete_receive_manual_return_data/<int:manu_ret_rec_dtl_id>/', views.deleteReceiveManualReturnData, name='delete_receive_manual_return_data'),
    path('Report_receive_manual_return/<int:manu_ret_rec_id>/', views.ReportReceiveManualReturnManagerAPI, name='Report_receive_manual_return'),
]
