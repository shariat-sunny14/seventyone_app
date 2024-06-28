from django.db import models
from organizations.models import organizationlst
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class UItemplate_setup(models.Model):
    uitemp_id = models.BigAutoField(primary_key=True, default=170100000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2uitemp_setup', on_delete=models.DO_NOTHING)
    uitemp_name = models.CharField(max_length=150, null=True, blank=True)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2uitemp_setup', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(auto_now_add=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1731000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2uitemp_setup', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=172350000000, editable=False)

    def save(self, *args, **kwargs):
        uitemp_data = UItemplate_setup.objects.all()

        if uitemp_data.exists() and self._state.adding:
            last_order = uitemp_data.latest('uitemp_id')
            user_session = uitemp_data.latest('ss_created_session')
            modifier_session = uitemp_data.latest('ss_modified_session')
            self.uitemp_id = int(last_order.uitemp_id) + 1
            self.ss_created_session = int(user_session.ss_created_session) + 1
            self.ss_modified_session = int(modifier_session.ss_modified_session) + 1
            
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.uitemp_id)