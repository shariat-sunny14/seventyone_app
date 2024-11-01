from django.db import models
from datetime import datetime
from django.utils import timezone
from django.db.models import Max
from organizations.models import branchslist, organizationlst
from store_setup.models import store
from item_setup.models import items
from registrations.models import in_registrations
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class local_purchase(models.Model):
    lp_id = models.BigAutoField(primary_key=True, default=2202022100000, editable=False)
    lp_no = models.CharField(max_length=15, editable=False)
    transaction_date = models.DateField(null=True, blank=True)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2lp_rec', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2lp_rec', on_delete=models.DO_NOTHING)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2lp_rec', on_delete=models.DO_NOTHING, editable=False)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2lp_rec', on_delete=models.DO_NOTHING)
    is_cash = models.BooleanField(default=False)
    is_credit = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2lp_rec', on_delete=models.DO_NOTHING)
    is_returned_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2is_lpret_by', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    returned_date = models.CharField(max_length=50, null=True, blank=True)
    invoice_no = models.CharField(max_length=50, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(max_length=300, default="", blank=True)
    cus_clients_name = models.CharField(max_length=250, null=True, blank=True)
    cus_mobile_number = models.CharField(max_length=20, null=True, blank=True)
    cus_gender = models.CharField(max_length=10, null=True, blank=True)
    cus_emrg_person = models.CharField(max_length=250, null=True, blank=True)
    cus_emrg_mobile = models.CharField(max_length=20, null=True, blank=True)
    cus_address = models.CharField(max_length=500, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2lp_rec', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1008888000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2lp_rec', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1009921000000, editable=False)


    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.id_org_id and self.branch_id_id:
                try:
                    # Get the maximum existing lp_id and increment by 1
                    latest_lp_id = local_purchase.objects.aggregate(Max('lp_id'))['lp_id__max']
                    if latest_lp_id is not None:
                        self.lp_id = latest_lp_id + 1
                    else:
                        self.lp_id = 2202022100000  # Initial value if no records exist

                    # Set the lp_no to "LPR" followed by current date and a unique number
                    current_date = datetime.now().strftime("%Y%m%d")
                    latest_lp_no = local_purchase.objects.filter(
                        id_org=self.id_org_id, 
                        branch_id=self.branch_id_id, 
                        lp_no__startswith=f"LPR{current_date}"
                    ).aggregate(Max('lp_no'))['lp_no__max']

                    if latest_lp_no is not None:
                        # Extract the last 4 digits of the lp_no and increment
                        latest_number = int(latest_lp_no[-4:]) + 1
                        lp_no_str = str(latest_number).zfill(4)
                    else:
                        lp_no_str = '0001'

                    self.lp_no = f"LPR{current_date}{lp_no_str}"

                    # Update session fields
                    user_session = local_purchase.objects.latest('ss_created_session')
                    modifier_session = local_purchase.objects.latest('ss_modified_session')

                    self.ss_created_session = user_session.ss_created_session + 1
                    self.ss_modified_session = modifier_session.ss_modified_session + 1

                except local_purchase.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.lp_id)
    


class local_purchasedtl(models.Model):
    lp_dtl_id = models.BigAutoField(primary_key=True, default=1005555000000, editable=False)
    lp_id = models.ForeignKey(local_purchase, null=True, blank=True, on_delete=models.DO_NOTHING, editable=False)
    lp_rec_date = models.DateField(blank=True, null=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2lp_recDtl', on_delete=models.DO_NOTHING, editable=False)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2lp_recDtl', on_delete=models.DO_NOTHING)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2lp_recDtl', on_delete=models.DO_NOTHING, editable=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    lp_rec_qty = models.FloatField(null=True, blank=True)
    unit_price = models.FloatField(null=True, blank=True)
    dis_percentage = models.FloatField(null=True, blank=True)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2lp_recDtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1363400000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2lp_recDtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=334791000000, editable=False)
    
    
    
    def save(self, *args, **kwargs):
        
        lp_dtl_data = local_purchasedtl.objects.all()

        if lp_dtl_data.exists() and self._state.adding:
            last_orderdtl = lp_dtl_data.latest('lp_dtl_id')
            user_session = lp_dtl_data.latest('ss_created_session')
            modifier_session = lp_dtl_data.latest('ss_modified_session')
            self.lp_dtl_id = int(last_orderdtl.lp_dtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.lp_dtl_id)