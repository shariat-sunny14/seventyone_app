from django.db import models
from organizations.models import branchslist, organizationlst
from local_purchase.models import local_purchase
from supplier_setup.models import suppliers
from store_setup.models import store
from item_setup.models import items
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class lp_return_details(models.Model):
    lprdtl_id = models.BigAutoField(primary_key=True, default=6677100000000, editable=False)
    lp_id = models.ForeignKey(local_purchase, null=True, blank=True, related_name='lp_id2lprdtl', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2lprdtl', on_delete=models.DO_NOTHING, editable=False)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2lprdtl', on_delete=models.DO_NOTHING, editable=False)
    lp_return_qty = models.FloatField(null=True, blank=True)
    is_cancel_qty = models.FloatField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    returned_date = models.CharField(max_length=150, null=True, blank=True)
    is_returned_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2lprdtl', on_delete=models.DO_NOTHING)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    returned_remarks = models.TextField(max_length=300, default="", blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2lprdtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=9916700000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2lprdtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=2267809000000, editable=False)

    def save(self, *args, **kwargs):
        
        lpdtls_data = lp_return_details.objects.all()

        if lpdtls_data.exists() and self._state.adding:
            last_orderdtl = lpdtls_data.latest('lprdtl_id')
            user_session = lpdtls_data.latest('ss_created_session')
            modifier_session = lpdtls_data.latest('ss_modified_session')
            self.lprdtl_id = int(last_orderdtl.lprdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.lprdtl_id)