from django.db import models
from organizations.models import branchslist, organizationlst
from purchase_order.models import purchase_order_list, purchase_orderdtls
from supplier_setup.models import suppliers
from store_setup.models import store
from item_setup.models import items
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class po_return_received_details(models.Model):
    porrecdtl_id = models.BigAutoField(primary_key=True, default=6610000000000, editable=False)
    po_id = models.ForeignKey(purchase_order_list, null=True, blank=True, related_name='po_id2porrecdtls', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2porrecdtls', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2porrecdtls', on_delete=models.DO_NOTHING, editable=False)
    ret_rec_qty = models.IntegerField(null=True, blank=True)
    is_return_received = models.BooleanField(default=False)
    return_received_date = models.CharField(max_length=150, null=True, blank=True)
    is_return_received_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2porrecdtls', on_delete=models.DO_NOTHING)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2porrecdtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=5501000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2porrecdtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=5501100000000, editable=False)

    def save(self, *args, **kwargs):
        
        porrecdtls_data = po_return_received_details.objects.all()

        if porrecdtls_data.exists() and self._state.adding:
            last_orderdtl = porrecdtls_data.latest('porrecdtl_id')
            user_session = porrecdtls_data.latest('ss_created_session')
            modifier_session = porrecdtls_data.latest('ss_modified_session')
            self.porrecdtl_id = int(last_orderdtl.porrecdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.porrecdtl_id)