from django.db import models
from organizations.models import branchslist, organizationlst
from purchase_order.models import purchase_order_list, purchase_orderdtls
from supplier_setup.models import suppliers
from store_setup.models import store
from item_setup.models import items
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class po_return_details(models.Model):
    poretdtl_id = models.BigAutoField(primary_key=True, default=5510000000000, editable=False)
    po_id = models.ForeignKey(purchase_order_list, null=True, blank=True, related_name='po_id2poretdtls', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2poretdtls', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2poretdtls', on_delete=models.DO_NOTHING, editable=False)
    return_qty = models.FloatField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    returned_date = models.CharField(max_length=150, null=True, blank=True)
    is_returned_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2poretdtls', on_delete=models.DO_NOTHING)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2poretdtls', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=4401000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2poretdtls', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=44011000000, editable=False)

    def save(self, *args, **kwargs):
        
        poretdtls_data = po_return_details.objects.all()

        if poretdtls_data.exists() and self._state.adding:
            last_orderdtl = poretdtls_data.latest('poretdtl_id')
            user_session = poretdtls_data.latest('ss_created_session')
            modifier_session = poretdtls_data.latest('ss_modified_session')
            self.poretdtl_id = int(last_orderdtl.poretdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.poretdtl_id)