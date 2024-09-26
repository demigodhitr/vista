# Generated by Django 5.0.6 on 2024-09-13 16:03

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_walletaddress_polygon_matic'),
    ]

    operations = [
        migrations.AddField(
            model_name='verification',
            name='date_submitted',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='walletaddress',
            name='polygon_matic',
            field=models.CharField(max_length=150, verbose_name='Company Polygon-matic Address'),
        ),
    ]
