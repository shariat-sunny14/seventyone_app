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
class manual_return_receive(models.Model):
    manu_ret_rec_id = models.BigAutoField(primary_key=True, default=9909099100000, editable=False)
    manu_ret_rec_no = models.CharField(max_length=15, editable=False)
    transaction_date = models.DateField(null=True, blank=True)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2manu_ter_rec', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2manu_ter_rec', on_delete=models.DO_NOTHING)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2manu_ter_rec', on_delete=models.DO_NOTHING, editable=False)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2manu_ter_rec', on_delete=models.DO_NOTHING)
    is_cash = models.BooleanField(default=False)
    is_credit = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2manu_ter_rec', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    invoice_no = models.CharField(max_length=50, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(max_length=300, default="", blank=True)
    cus_clients_name = models.CharField(max_length=250, null=True, blank=True)
    cus_mobile_number = models.CharField(max_length=20, null=True, blank=True)
    cus_gender = models.CharField(max_length=10, null=True, blank=True)
    cus_emrg_person = models.CharField(max_length=250, null=True, blank=True)
    cus_emrg_mobile = models.CharField(max_length=20, null=True, blank=True)
    cus_address = models.CharField(max_length=500, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2manu_ter_rec', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1008888000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2manu_ter_rec', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1009921000000, editable=False)


    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.id_org_id and self.branch_id_id:
                try:
                    # Get the maximum existing manu_ret_rec_id and increment by 1
                    latest_manu_ret_rec_id = manual_return_receive.objects.aggregate(Max('manu_ret_rec_id'))['manu_ret_rec_id__max']
                    if latest_manu_ret_rec_id is not None:
                        self.manu_ret_rec_id = latest_manu_ret_rec_id + 1
                    else:
                        self.manu_ret_rec_id = 9909099100000  # Initial value if no records exist

                    # Set the manu_ret_rec_no to "MRR" followed by current date and a unique number
                    current_date = datetime.now().strftime("%Y%m%d")
                    latest_manu_ret_rec_no = manual_return_receive.objects.filter(
                        id_org=self.id_org_id, 
                        branch_id=self.branch_id_id, 
                        manu_ret_rec_no__startswith=f"MRR{current_date}"
                    ).aggregate(Max('manu_ret_rec_no'))['manu_ret_rec_no__max']

                    if latest_manu_ret_rec_no is not None:
                        # Extract the last 4 digits of the manu_ret_rec_no and increment
                        latest_number = int(latest_manu_ret_rec_no[-4:]) + 1
                        manu_ret_rec_no_str = str(latest_number).zfill(4)
                    else:
                        manu_ret_rec_no_str = '0001'

                    self.manu_ret_rec_no = f"MRR{current_date}{manu_ret_rec_no_str}"

                    # Update session fields
                    user_session = manual_return_receive.objects.latest('ss_created_session')
                    modifier_session = manual_return_receive.objects.latest('ss_modified_session')

                    self.ss_created_session = user_session.ss_created_session + 1
                    self.ss_modified_session = modifier_session.ss_modified_session + 1

                except manual_return_receive.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.manu_ret_rec_id)
    

class manual_return_receivedtl(models.Model):
    manu_ret_rec_dtl_id = models.BigAutoField(primary_key=True, default=8008588000000, editable=False)
    manu_ret_rec_id = models.ForeignKey(manual_return_receive, null=True, blank=True, on_delete=models.DO_NOTHING, editable=False)
    manu_ret_rec_date = models.DateField(blank=True, null=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2manu_ter_recDtl', on_delete=models.DO_NOTHING, editable=False)
    reg_id = models.ForeignKey(in_registrations, null=True, blank=True, related_name='reg_id2manu_ter_recDtl', on_delete=models.DO_NOTHING)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2manu_ter_recDtl', on_delete=models.DO_NOTHING, editable=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    manu_ret_rec_qty = models.FloatField(null=True, blank=True)
    unit_price = models.FloatField(null=True, blank=True)
    dis_percentage = models.FloatField(null=True, blank=True)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    item_exp_date = models.DateField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2manu_ter_recDtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1469400000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2manu_ter_recDtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=674891000000, editable=False)
    
    
    def save(self, *args, **kwargs):
        
        dtl_data = manual_return_receivedtl.objects.all()

        if dtl_data.exists() and self._state.adding:
            last_orderdtl = dtl_data.latest('manu_ret_rec_dtl_id')
            user_session = dtl_data.latest('ss_created_session')
            modifier_session = dtl_data.latest('ss_modified_session')
            self.manu_ret_rec_dtl_id = int(last_orderdtl.manu_ret_rec_dtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.manu_ret_rec_dtl_id)