from django.db import models
from datetime import datetime
from django.utils import timezone
from pytz import timezone as tz
from organizations.models import branchslist, organizationlst
from bank_setup.models import bank_lists
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
class daily_bank_statement(models.Model):
    deposit_id = models.BigAutoField(primary_key=True, default=1555000000000, editable=False)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2bankstatement', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2bankstatement', on_delete=models.DO_NOTHING)
    sub_branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='sub_branch_id2bankstatement', on_delete=models.DO_NOTHING)
    main_branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='main_branch_id2bankstatement', on_delete=models.DO_NOTHING)
    bank_id = models.ForeignKey(bank_lists, null=True, blank=True, related_name='bank_id2bankstatement', on_delete=models.DO_NOTHING)
    deposits_amt = models.FloatField(default=0, blank=True)
    types_deposit = models.CharField(max_length=50, null=True, blank=True)
    pay_methord = models.CharField(max_length=50, null=True, blank=True)
    deposit_reason = models.CharField(max_length=250, null=True, blank=True)
    deposit_date = models.DateField(null=True, blank=True)
    is_bank_statement = models.BooleanField(default=False)
    is_branch_deposit = models.BooleanField(default=False)
    is_branch_deposit_receive = models.BooleanField(default=False)
    ss_creator = models.ForeignKey(User, null=True, blank=True, related_name='ss_creator2bankstatement', on_delete=models.DO_NOTHING, editable=False)
    ss_created_on = models.DateTimeField(editable=False, null=True, blank=True)
    ss_created_session = models.BigIntegerField(null=True, blank=True, default=1686000000000, editable=False)
    ss_modifier = models.ForeignKey(User, null=True, blank=True, related_name='ss_modifier2bankstatement', on_delete=models.DO_NOTHING)
    ss_modified_on = models.DateTimeField(auto_now=True)
    ss_modified_session = models.BigIntegerField(null=True, blank=True, default=148830000000, editable=False)

    
    def save(self, *args, **kwargs):
        if self._state.adding:
            dhaka_tz = tz('Asia/Dhaka')
            self.ss_created_on = timezone.now().astimezone(dhaka_tz)

            # Autoincrement IDs and session fields
            last_order = daily_bank_statement.objects.latest('deposit_id') if daily_bank_statement.objects.exists() else None
            last_user_session = daily_bank_statement.objects.latest('ss_created_session') if daily_bank_statement.objects.exists() else None
            last_modifier_session = daily_bank_statement.objects.latest('ss_modified_session') if daily_bank_statement.objects.exists() else None

            self.deposit_id = last_order.deposit_id + 1 if last_order else 1555000000000
            self.ss_created_session = last_user_session.ss_created_session + 1 if last_user_session else 1686000000000
            self.ss_modified_session = last_modifier_session.ss_modified_session + 1 if last_modifier_session else 148830000000

        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.deposit_id)


class cash_on_hands(models.Model):
    on_cash_id = models.BigAutoField(primary_key=True, default=122122000000, editable=False)
    on_hand_cash = models.FloatField(default=0, blank=True)
    org_id = models.ForeignKey(organizationlst, null=True, blank=True, related_name='org_id2on_cash_hand', on_delete=models.DO_NOTHING)
    branch_id = models.ForeignKey(branchslist, null=True, blank=True, related_name='branch_id2on_cash_hand', on_delete=models.DO_NOTHING)

    def __str__(self):
        return str(self.on_cash_id)
    
    def save(self, *args, **kwargs):
        
        on_cash_data = cash_on_hands.objects.all()

        if on_cash_data.exists() and self._state.adding:
            last_orderdtl = on_cash_data.latest('on_cash_id')
            self.on_cash_id = int(last_orderdtl.on_cash_id) + 1
            
        super().save(*args, **kwargs)