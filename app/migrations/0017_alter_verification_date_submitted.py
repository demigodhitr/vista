# Generated by Django 5.0.6 on 2024-09-13 16:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_verification_date_submitted_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='verification',
            name='date_submitted',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
