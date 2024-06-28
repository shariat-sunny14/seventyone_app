from django.db import models
from organizations.models import branchslist, organizationlst
from item_setup.models import items
from department.models import departmentlst
from supplier_setup.models import suppliers
from django.contrib.auth import get_user_model
User = get_user_model()


# b2b client item percentage models
class b2b_client_item_percentage(models.Model):
    item_per_id = models.BigAutoField(primary_key=True, default=1022550000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2b2bitem_perc', on_delete=models.DO_NOTHING)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2b2bitem_perc', on_delete=models.DO_NOTHING)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2b2bitem_perc', on_delete=models.DO_NOTHING)
    b2b_item_perc = models.IntegerField(null=True, blank=True)
    b2b_item_amt = models.IntegerField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2b2bitem_perc', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1961000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2b2bitem_perc', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1985100000000, editable=False)
    
    def save(self, *args, **kwargs):
        model_data = b2b_client_item_percentage.objects.all()

        if model_data.exists() and self._state.adding:
            last_order = model_data.latest('item_per_id')
            user_session = model_data.latest('ss_created_session')
            modifier_session = model_data.latest('ss_modified_session')
            self.item_per_id = int(last_order.item_per_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return str(self.item_per_id)
    


# b2b client Dept percentage models
class b2b_client_dept_percentage(models.Model):
    dept_per_id = models.BigAutoField(primary_key=True, default=1033550000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2b2bdept_perc', on_delete=models.DO_NOTHING)
    dept_id = models.ForeignKey(departmentlst, null=True, blank=True, related_name='dept_id2b2bdept_perc', on_delete=models.DO_NOTHING)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2b2bdept_perc', on_delete=models.DO_NOTHING)
    b2b_dept_perc = models.IntegerField(null=True, blank=True)
    b2b_dept_amt = models.IntegerField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2b2bdept_perc', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1451000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2b2bdept_perc', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1385100000000, editable=False)
    
    def save(self, *args, **kwargs):
        model_data = b2b_client_dept_percentage.objects.all()

        if model_data.exists() and self._state.adding:
            last_order = model_data.latest('dept_per_id')
            user_session = model_data.latest('ss_created_session')
            modifier_session = model_data.latest('ss_modified_session')
            self.dept_per_id = int(last_order.dept_per_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return str(self.dept_per_id)
    


# b2b client item rate models
class b2b_client_item_rates(models.Model):
    b2b_clitr_id = models.BigAutoField(primary_key=True, default=1133440000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2b2bclir_id', on_delete=models.DO_NOTHING)
    item_id = models.ForeignKey(items, null=True, blank=True, related_name='item_id2b2bclir_id', on_delete=models.DO_NOTHING)
    supplier_id = models.ForeignKey(suppliers, null=True, blank=True, related_name='supplier_id2b2bclir_id', on_delete=models.DO_NOTHING)
    b2b_client_rate = models.IntegerField(null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2b2bclir_id', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1877000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2b2bclir_id', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1556600000000, editable=False)
    
    def save(self, *args, **kwargs):
        b2bclitr_data = b2b_client_item_rates.objects.all()

        if b2bclitr_data.exists() and self._state.adding:
            last_order = b2bclitr_data.latest('b2b_clitr_id')
            user_session = b2bclitr_data.latest('ss_created_session')
            modifier_session = b2bclitr_data.latest('ss_modified_session')
            self.b2b_clitr_id = int(last_order.b2b_clitr_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return str(self.b2b_clitr_id)