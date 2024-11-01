from django.db import models
from datetime import datetime
from django.db.models import Max
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class in_registrations(models.Model):
    reg_id = models.BigAutoField(primary_key=True, default=1112200000000, editable=False)
    customer_no = models.CharField(max_length=15, editable=False, null=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2in_reg', on_delete=models.DO_NOTHING)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    marital_status = models.CharField(max_length=10, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    dateofbirth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True)
    patient_type = models.CharField(max_length=30, null=True, blank=True)
    co_name = models.CharField(max_length=100, null=True, blank=True)
    co_relationship = models.CharField(max_length=30, null=True, blank=True)
    co_mobile_number = models.CharField(max_length=15, null=True, blank=True)
    division = models.CharField(max_length=20, null=True, blank=True)
    district = models.CharField(max_length=20, null=True, blank=True)
    thana_upazila = models.CharField(max_length=30, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    occupation = models.CharField(max_length=30, null=True, blank=True)
    religion = models.CharField(max_length=20, null=True, blank=True)
    nationality = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=20, null=True, blank=True)
    identity_mark = models.CharField(max_length=50, null=True, blank=True)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_con_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_con_mobile = models.CharField(max_length=15, null=True, blank=True)
    emergency_con_rel = models.CharField(max_length=30, null=True, blank=True)
    emergency_con_address = models.CharField(max_length=250, null=True, blank=True)
    customer_img = models.ImageField(upload_to='in_reg_profile', max_length=50, null=True, blank=True)
    reg_date = models.DateField(default=datetime.now, editable=False)
    is_active = models.BooleanField(default=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2in_reg', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1990800000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2in_reg', on_delete=models.DO_NOTHING, editable=False)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=1529200000000, editable=False)


    class Meta:
        unique_together = ('reg_id', 'customer_no')


    def save(self, *args, **kwargs):
        if self._state.adding:  # New object
            latest_reg_id = in_registrations.objects.aggregate(Max('reg_id'))['reg_id__max']
            self.reg_id = latest_reg_id + 1 if latest_reg_id else 1112200000000

            # Generate unique customer_no within the same organization
            latest_customer_no = in_registrations.objects.filter(
                org_id=self.org_id,
                customer_no__startswith="CN"
            ).aggregate(Max('customer_no'))['customer_no__max']

            if latest_customer_no:
                latest_number = int(latest_customer_no[2:]) + 1
                customer_no_str = str(latest_number).zfill(11)
            else:
                customer_no_str = '00000000001'

            self.customer_no = f"CN{customer_no_str}"

            # Fetch and increment session fields
            latest_created_session = in_registrations.objects.aggregate(Max('ss_created_session'))['ss_created_session__max']
            self.ss_created_session = latest_created_session + 1 if latest_created_session else 1990800000001

            latest_modified_session = in_registrations.objects.aggregate(Max('ss_modified_session'))['ss_modified_session__max']
            self.ss_modified_session = latest_modified_session + 1 if latest_modified_session else 1529200000001

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.reg_id)