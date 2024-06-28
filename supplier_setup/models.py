from django.db import models
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
# Suppliers models
class suppliers(models.Model):
    supplier_id = models.BigAutoField(primary_key=True, default=122090000000, editable=False)
    supplier_no = models.CharField(max_length=100, null=True, blank=True)
    supplier_name = models.CharField(max_length=200, null=True, blank=True)
    company_name = models.CharField(max_length=200, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2suppliers', on_delete=models.DO_NOTHING)
    description = models.CharField(max_length=500, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    supplier_flag = models.IntegerField(null=True, blank=True, default=0)
    manufacturer_flag = models.IntegerField(null=True, blank=True, default=0)
    b2bclient_flag = models.IntegerField(null=True, blank=True, default=0)
    phone = models.BigIntegerField(null=True, blank=True)
    mobile = models.CharField(max_length=50, null=True, blank=True)
    supplier_email = models.EmailField(null=True, blank=True)
    supplier_fax = models.CharField(max_length=100, null=True, blank=True)
    supplier_web = models.CharField(max_length=100, null=True, blank=True)
    account_no = models.CharField(max_length=50, null=True, blank=True)
    supplier_remarks = models.CharField(max_length=500, null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    con_per_Phone = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2suppliers', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1230000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2suppliers', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112300000000, editable=False)

    
    def save(self, *args, **kwargs):
        supplier_data = suppliers.objects.all()

        if supplier_data.exists() and self._state.adding:
            last_order = supplier_data.latest('supplier_id')
            user_session = supplier_data.latest('ss_created_session')
            modifier_session = supplier_data.latest('ss_modified_session')
            self.supplier_id = int(last_order.supplier_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return str(self.supplier_id)


# Manufacturer models
class manufacturer(models.Model):
    manufac_id = models.BigAutoField(primary_key=True, default=123010000000, editable=False)
    manufac_no = models.CharField(max_length=100, unique=True)
    manufac_name = models.CharField(max_length=200, unique=True)
    company_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    manufacturer_flag = models.BooleanField(default=False)
    foreign_flag = models.BooleanField(default=False)
    phone = models.CharField(max_length=50, null=True, blank=True)
    mobile = models.CharField(max_length=50, null=True, blank=True)
    manufac_email = models.EmailField(null=True, blank=True)
    manufac_fax = models.CharField(max_length=100, null=True, blank=True)
    manufac_web = models.CharField(max_length=100, null=True, blank=True)
    account_no = models.CharField(max_length=50, null=True, blank=True)
    manufac_remarks = models.CharField(max_length=500, null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    con_per_Phone = models.CharField(max_length=50, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2manufacturer', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1230000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2manufacturer', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=112300000000, editable=False)

    
    def save(self, *args, **kwargs):
        manufac = manufacturer.objects.all()

        if manufac.exists() and self._state.adding:
            last_order = manufac.latest('manufac_id')
            user_session = manufac.latest('ss_created_session')
            modifier_session = manufac.latest('ss_modified_session')
            self.manufac_id = int(last_order.manufac_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f'{self.manufac_no} {self.manufac_name}'