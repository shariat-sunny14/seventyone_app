# Generated by Django 4.1.5 on 2024-10-18 15:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_setup', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('drivers_setup', '0002_initial'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='drivers_list',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='country2driverslist', to='user_setup.lookup_values'),
        ),
        migrations.AddField(
            model_name='drivers_list',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='district2driverslist', to='user_setup.lookup_values'),
        ),
        migrations.AddField(
            model_name='drivers_list',
            name='division',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='division2driverslist', to='user_setup.lookup_values'),
        ),
        migrations.AddField(
            model_name='drivers_list',
            name='org_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='org_id2driverslist', to='organizations.organizationlst'),
        ),
        migrations.AddField(
            model_name='drivers_list',
            name='ss_creator',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_creator2driverslist', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='drivers_list',
            name='ss_modifier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ss_modifier2driverslist', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='drivers_list',
            name='upazila',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='upazila2driverslist', to='user_setup.lookup_values'),
        ),
    ]
