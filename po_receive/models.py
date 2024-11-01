from django.db import models
from organizations.models import branchslist, organizationlst
from purchase_order.models import purchase_order_list, purchase_orderdtls
from supplier_setup.models import suppliers
from store_setup.models import store
from item_setup.models import items
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class po_receive_details(models.Model):
    pordtl_id = models.BigAutoField(primary_key=True, default=4410000000000, editable=False)
    po_id = models.ForeignKey(purchase_order_list, null=True, blank=True, related_name='po_id2pordtls', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2pordtls', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2pordtls', on_delete=models.DO_NOTHING, editable=False)
    receive_qty = models.FloatField(null=True, blank=True)
    bonus_qty = models.FloatField(null=True, blank=True)
    is_received = models.BooleanField(default=False)
    received_date = models.CharField(max_length=150, null=True, blank=True)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    is_received_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2pordtls', on_delete=models.DO_NOTHING)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2pordtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=3301000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2pordtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=33011000000, editable=False)

    def save(self, *args, **kwargs):
        
        pordtls_data = po_receive_details.objects.all()

        if pordtls_data.exists() and self._state.adding:
            last_orderdtl = pordtls_data.latest('pordtl_id')
            user_session = pordtls_data.latest('ss_created_session')
            modifier_session = pordtls_data.latest('ss_modified_session')
            self.pordtl_id = int(last_orderdtl.pordtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.pordtl_id)
