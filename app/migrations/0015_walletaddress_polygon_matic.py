# Generated by Django 5.0.6 on 2024-09-02 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_walletaddress_lite_coin_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='walletaddress',
            name='polygon_matic',
            field=models.CharField(default='', max_length=150, verbose_name='Company Polugon-matic Address'),
            preserve_default=False,
        ),
    ]
