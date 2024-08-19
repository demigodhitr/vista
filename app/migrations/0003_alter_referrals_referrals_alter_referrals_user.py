# Generated by Django 5.0.6 on 2024-06-23 07:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_referrals'),
    ]

    operations = [
        migrations.AlterField(
            model_name='referrals',
            name='referrals',
            field=models.ManyToManyField(blank=True, related_name='my_referrals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='referrals',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
