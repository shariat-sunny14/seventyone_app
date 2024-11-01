# Generated by Django 4.1.5 on 2024-10-18 15:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UItemplate_setup',
            fields=[
                ('uitemp_id', models.BigAutoField(default=170100000000, editable=False, primary_key=True, serialize=False)),
                ('uitemp_name', models.CharField(blank=True, max_length=150, null=True)),
                ('ss_created_on', models.DateTimeField(auto_now_add=True)),
                ('ss_created_session', models.BigIntegerField(blank=True, default=1731000000000, editable=False, null=True)),
                ('ss_modified_on', models.DateTimeField(auto_now=True)),
                ('ss_modified_session', models.BigIntegerField(blank=True, default=172350000000, editable=False, null=True)),
                ('org_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='org_id2uitemp_setup', to='organizations.organizationlst')),
            ],
        ),
    ]
