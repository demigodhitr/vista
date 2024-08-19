# Generated by Django 5.0.6 on 2024-08-01 11:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_tradingjournals'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JournalPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_date', models.DateTimeField(auto_now_add=True)),
                ('price_at_purchase', models.DecimalField(decimal_places=2, max_digits=10)),
                ('confirm_purchase', models.BooleanField(default=False)),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.tradingjournals')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
