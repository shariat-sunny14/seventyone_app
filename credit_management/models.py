from django.db import models
from organizations.models import branchslist, organizationlst
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()

# credit Transactions models
class credit_transactions(models.Model):
    credit_id = models.BigAutoField(primary_key=True, default=1122330000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2credit_trans', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2credit_trans', on_delete=models.DO_NOTHING)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2credit_trans', on_delete=models.DO_NOTHING)
    credit_payment = models.IntegerField(null=True, blank=True)
    is_debited = models.BooleanField(default=False)
    is_credited = models.BooleanField(default=False)
    credit_pay_date = models.DateField(auto_now_add=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2credit_trans', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1888000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2credit_trans', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1889900000000, editable=False)

    
    def save(self, *args, **kwargs):
        credit_data = credit_transactions.objects.all()

        if credit_data.exists() and self._state.adding:
            last_order = credit_data.latest('credit_id')
            user_session = credit_data.latest('ss_created_session')
            modifier_session = credit_data.latest('ss_modified_session')
            self.credit_id = int(last_order.credit_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return str(self.credit_id)