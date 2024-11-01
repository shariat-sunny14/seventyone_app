from django.db import models
from datetime import datetime
from django.db.models import Max
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()
from store_setup.models import store
from item_setup.models import items

# Create your models here.
class item_reconciliation(models.Model):
    recon_id = models.BigAutoField(primary_key=True, default=1234300000000, editable=False)
    recon_no = models.CharField(max_length=15, editable=False)
    recon_type = models.IntegerField(null=True, blank=True)
    recon_date = models.DateField(default=datetime.now, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2recon', on_delete=models.DO_NOTHING, editable=False)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2recon', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2recon', on_delete=models.DO_NOTHING)
    approved_date = models.DateField(null=True, blank=True, editable=False)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2recon', on_delete=models.DO_NOTHING)
    description = models.TextField(max_length=300, default="", blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2recon', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1456000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2recon', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=103060000000, editable=False)


    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.id_org_id and self.branch_id_id:
                try:
                    # Get the maximum existing recon_id and increment by 1
                    latest_recon_id = item_reconciliation.objects.aggregate(Max('recon_id'))['recon_id__max']
                    if latest_recon_id is not None:
                        self.recon_id = latest_recon_id + 1
                    else:
                        self.recon_id = 1234300000000  # Initial value if no records exist

                    # Set the recon_no to "RC" followed by current date and a unique number
                    current_date = datetime.now().strftime("%Y%m%d")
                    latest_recon_no = item_reconciliation.objects.filter(
                        id_org=self.id_org_id, 
                        branch_id=self.branch_id_id, 
                        recon_no__startswith=f"RC{current_date}"
                    ).aggregate(Max('recon_no'))['recon_no__max']

                    if latest_recon_no is not None:
                        # Extract the last 4 digits of the recon_no and increment
                        latest_number = int(latest_recon_no[-4:]) + 1
                        recon_no_str = str(latest_number).zfill(4)
                    else:
                        recon_no_str = '0001'

                    self.recon_no = f"RC{current_date}{recon_no_str}"

                    # Update session fields
                    user_session = item_reconciliation.objects.latest('ss_created_session')
                    modifier_session = item_reconciliation.objects.latest('ss_modified_session')

                    self.ss_created_session = user_session.ss_created_session + 1
                    self.ss_modified_session = modifier_session.ss_modified_session + 1

                except item_reconciliation.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.recon_id)

    
class item_reconciliationdtl(models.Model):
    recondtl_id = models.BigAutoField(primary_key=True, default=1553000000000, editable=False)
    recon_id = models.ForeignKey(item_reconciliation, null=True, blank=True, related_name='recon_id_id', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2recondtl', on_delete=models.DO_NOTHING, editable=False)
    recondtl_date = models.DateField(null=True, blank=True)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2recondtl', on_delete=models.DO_NOTHING, editable=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.DateField(null=True, blank=True, editable=False)
    recon_qty = models.CharField(max_length=150, null=True, blank=True)
    unit_price = models.IntegerField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2recondtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1053000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2recondtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=104210000000, editable=False)
    
    def __str__(self):
        return str(self.recondtl_id)
    
    def save(self, *args, **kwargs):
        
        recondtl_data = item_reconciliationdtl.objects.all()

        if recondtl_data.exists() and self._state.adding:
            last_orderdtl = recondtl_data.latest('recondtl_id')
            user_session = recondtl_data.latest('ss_created_session')
            modifier_session = recondtl_data.latest('ss_modified_session')
            self.recondtl_id = int(last_orderdtl.recondtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)