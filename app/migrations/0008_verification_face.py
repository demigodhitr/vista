# Generated by Django 5.0.6 on 2024-08-17 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_alter_balanceeur_deposits_alter_balanceusd_deposits_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='verification',
            name='face',
            field=models.ImageField(blank=True, null=True, upload_to='id_cards/faces/'),
        ),
    ]
