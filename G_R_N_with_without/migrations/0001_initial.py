# Generated by Django 4.1.5 on 2024-10-18 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='without_GRN',
            fields=[
                ('wo_grn_id', models.BigAutoField(default=1901010000000, editable=False, primary_key=True, serialize=False)),
                ('wo_grn_no', models.CharField(editable=False, max_length=15)),
                ('transaction_date', models.DateField(blank=True, null=True)),
                ('is_cash', models.BooleanField(default=False)),
                ('is_credit', models.BooleanField(default=False)),
                ('is_approved', models.BooleanField(default=False)),
                ('approved_date', models.CharField(blank=True, max_length=50, null=True)),
                ('invoice_no', models.CharField(blank=True, max_length=50, null=True)),
                ('invoice_date', models.DateField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True, default='', max_length=300)),
                ('ss_created_on', models.DateTimeField(auto_now_add=True)),
                ('ss_created_session', models.BigIntegerField(blank=True, default=1007000000000, editable=False, null=True)),
                ('ss_modified_on', models.DateTimeField(auto_now=True)),
                ('ss_modified_session', models.BigIntegerField(blank=True, default=1006100000000, editable=False, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='without_GRNdtl',
            fields=[
                ('wo_grndtl_id', models.BigAutoField(default=100410000000, editable=False, primary_key=True, serialize=False)),
                ('wo_grn_date', models.DateField(blank=True, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('approved_date', models.CharField(blank=True, max_length=50, null=True)),
                ('wo_grn_qty', models.FloatField(blank=True, null=True)),
                ('unit_price', models.FloatField(blank=True, null=True)),
                ('item_batch', models.CharField(blank=True, max_length=150, null=True)),
                ('item_exp_date', models.DateField(blank=True, null=True)),
                ('ss_created_on', models.DateTimeField(auto_now_add=True)),
                ('ss_created_session', models.BigIntegerField(blank=True, default=1291000000000, editable=False, null=True)),
                ('ss_modified_on', models.DateTimeField(auto_now=True)),
                ('ss_modified_session', models.BigIntegerField(blank=True, default=112950000000, editable=False, null=True)),
            ],
        ),
    ]
