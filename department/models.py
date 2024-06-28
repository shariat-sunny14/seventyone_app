from datetime import datetime
from django.utils import timezone
from pytz import timezone as tz
from django.db import models
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.
class departmentlst(models.Model):
    dept_id = models.BigAutoField(primary_key=True, default=101011000000, editable=False)
    dept_no = models.CharField(max_length=50, null=True, blank=True)
    is_parent_dept = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    dept_name = models.CharField(max_length=200, null=True, blank=True)
    parent_dept_id = models.ForeignKey('self', null=True, blank=True, related_name='dept_id2deptlst', on_delete=models.DO_NOTHING, editable=False)
    id_org = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2deptlst', on_delete=models.DO_NOTHING)
    alias = models.CharField(max_length=150, null=True, blank=True)
    level = models.CharField(max_length=150, null=True, blank=True)
    Report_sl_no = models.CharField(max_length=150, null=True, blank=True)
    financebusiness_area = models.CharField(max_length=150, null=True, blank=True)
    unitflag_descr = models.CharField(max_length=300, null=True, blank=True)
    ipd_dept_flag = models.BooleanField(default=False)
    opd_dept_flag = models.BooleanField(default=False)
    daycare_flag = models.BooleanField(default=False)
    clinical_flag = models.BooleanField(default=False)
    hr_flag = models.BooleanField(default=False)
    film_required = models.BooleanField(default=False)
    billing_flag = models.BooleanField(default=False)
    dept_bill_activation = models.BooleanField(default=False)
    district  = models.CharField(max_length=100, null=True, blank=True)
    category  = models.CharField(max_length=100, null=True, blank=True)
    location  = models.CharField(max_length=100, null=True, blank=True)
    grade = models.CharField(max_length=100, null=True, blank=True)
    opening_date = models.DateField(default=datetime.now, null=True, blank=True)
    location_type = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    fax = models.CharField(max_length=100, null=True, blank=True)
    website = models.CharField(max_length=100, null=True, blank=True)
    hotline = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    unit_details_descr = models.CharField(max_length=300, null=True, blank=True)
    ss_creator = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_creator2deptlst', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True)
    ss_created_session = models.BigIntegerField(
        null=True, blank=True, default=1266770000000, editable=False)
    ss_modifier = models.ForeignKey(
        User, null=True, blank=True, related_name='ss_modifier2deptlst', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(
        null=True, blank=True, default=1266880000000, editable=False)


    def __str__(self):
        return str(self.dept_id)

    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = departmentlst.objects.latest(
                'dept_id') if departmentlst.objects.exists() else None
            last_user_session = departmentlst.objects.latest(
                'ss_created_session') if departmentlst.objects.exists() else None
            last_modifier_session = departmentlst.objects.latest(
                'ss_modified_session') if departmentlst.objects.exists() else None

            self.dept_id = last_order.dept_id + 1 if last_order else 101011000000
            self.ss_created_session = last_user_session.ss_created_session + \
                1 if last_user_session else 1266770000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + \
                1 if last_modifier_session else 1266880000000

        super().save(*args, **kwargs)