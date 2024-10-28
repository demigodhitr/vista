# Generated by Django 5.0.6 on 2024-10-11 16:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_investments_last_updated_alter_investments_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='investments',
            name='days_remaining',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='investments',
            name='last_decrement',
            field=models.DateField(blank=True, editable=False, null=True),
        ),
        migrations.CreateModel(
            name='EarningsHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profit_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                ('investment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.investments')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]