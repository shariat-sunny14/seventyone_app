from django.db import models
from organizations.models import branchslist, organizationlst
from user_setup.models import lookup_values
from django.contrib.auth import get_user_model
User = get_user_model()


# organizations list models here.
class drivers_list(models.Model):
    driver_id = models.BigAutoField(primary_key=True, default=1919100000000, editable=False)
    driver_no = models.CharField(max_length=50, null=True, blank=True)
    driver_name = models.CharField(max_length=200, null=True, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2driverslist', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2driverslist', on_delete=models.DO_NOTHING)
    country = models.ForeignKey(lookup_values, null=True, blank=True, related_name='country2driverslist', on_delete=models.DO_NOTHING)
    division = models.ForeignKey(lookup_values, null=True, blank=True, related_name='division2driverslist', on_delete=models.DO_NOTHING)
    district = models.ForeignKey(lookup_values, null=True, blank=True, related_name='district2driverslist', on_delete=models.DO_NOTHING)
    upazila = models.ForeignKey(lookup_values, null=True, blank=True, related_name='upazila2driverslist', on_delete=models.DO_NOTHING)
    email = models.CharField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=200, null=True, blank=True)
    website = models.CharField(max_length=200, null=True, blank=True)
    hotline = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    driver_picture = models.ImageField(upload_to='driver_picture', max_length=100, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2driverslist', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=19900000000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2driverslist', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=18899000000000, editable=False)

    def save(self, *args, **kwargs):
        driver_data = drivers_list.objects.all()

        if driver_data.exists() and self._state.adding:
            last_order = driver_data.latest('driver_id')
            user_session = driver_data.latest('ss_created_session')
            modifier_session = driver_data.latest('ss_modified_session')
            self.driver_id = int(last_order.driver_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.driver_id)
