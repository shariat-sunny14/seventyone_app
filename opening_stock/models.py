from django.db import models
from datetime import datetime
from django.db.models import Max
from organizations.models import branchslist, organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()
from store_setup.models import store
from item_setup.models import items

# Create your models here.
class opening_stock(models.Model):
    op_st_id = models.BigAutoField(primary_key=True, default=1239010000000, editable=False)
    op_no = models.CharField(max_length=15, editable=False)
    transaction_date = models.DateField(null=True, blank=True)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2opst', on_delete=models.DO_NOTHING, editable=False)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2opst', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2opst', on_delete=models.DO_NOTHING)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_approved_by = models.ForeignKey(User, null=True, blank=True, related_name='user_id2opst', on_delete=models.DO_NOTHING)
    remarks = models.TextField(max_length=300, default="", blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2opst', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1291000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2opst', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112950000000, editable=False)


    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.id_org_id and self.branch_id_id:
                try:
                    # Get the maximum existing op_st_id and increment by 1
                    latest_op_st_id = opening_stock.objects.aggregate(Max('op_st_id'))['op_st_id__max']
                    if latest_op_st_id is not None:
                        self.op_st_id = latest_op_st_id + 1
                    else:
                        self.op_st_id = 1239010000000  # Initial value if no records exist

                    # Set the op_no to "OP" followed by current date and a unique number
                    current_date = datetime.now().strftime("%Y%m%d")
                    latest_op_no = opening_stock.objects.filter(id_org=self.id_org_id, branch_id=self.branch_id_id, op_no__startswith=f"OP{current_date}").aggregate(Max('op_no'))['op_no__max']
                    if latest_op_no is not None:
                        latest_po_number = int(latest_op_no[9:]) + 1
                        op_no_str = str(latest_po_number).zfill(4)
                    else:
                        op_no_str = '0001'
                    self.op_no = f"OP{current_date}{op_no_str}"

                    user_session = opening_stock.objects.latest('ss_created_session')
                    modifier_session = opening_stock.objects.latest('ss_modified_session')

                    self.ss_created_session = user_session.ss_created_session + 1
                    self.ss_modified_session = modifier_session.ss_modified_session + 1

                except opening_stock.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.op_st_id)

    
    

class opening_stockdtl(models.Model):
    op_stdtl_id = models.BigAutoField(primary_key=True, default=12400000000, editable=False)
    op_st_id = models.ForeignKey(opening_stock, null=True, blank=True, related_name='opening_stock_id', on_delete=models.DO_NOTHING, editable=False)
    store_id = models.ForeignKey(store, null=True, blank=True, related_name='store_id2opening_stockdtl', on_delete=models.DO_NOTHING, editable=False)
    opening_date = models.DateField(null=True, blank=True)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2opening_stockdtl', on_delete=models.DO_NOTHING, editable=False)
    is_approved = models.BooleanField(default=False)
    approved_date = models.CharField(max_length=50, null=True, blank=True)
    op_item_qty = models.CharField(max_length=150, null=True, blank=True)
    unit_price = models.IntegerField(null=True, blank=True)
    item_batch = models.CharField(max_length=150, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2opening_stockdtl', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1291000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2opening_stockdtl', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112950000000, editable=False)
    
    def __str__(self):
        return str(self.op_stdtl_id)
    
    def save(self, *args, **kwargs):
        
        stockdtl_data = opening_stockdtl.objects.all()

        if stockdtl_data.exists() and self._state.adding:
            last_orderdtl = stockdtl_data.latest('op_stdtl_id')
            user_session = stockdtl_data.latest('ss_created_session')
            modifier_session = stockdtl_data.latest('ss_modified_session')
            self.op_stdtl_id = int(last_orderdtl.op_stdtl_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1

        super().save(*args, **kwargs)

    