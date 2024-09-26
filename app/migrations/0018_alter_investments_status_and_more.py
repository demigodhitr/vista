# Generated by Django 5.0.6 on 2024-09-14 21:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_alter_verification_date_submitted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='investments',
            name='status',
            field=models.CharField(choices=[('rejected', 'Rejected'), ('In progress', 'In progress'), ('completed', 'Completed')], default='awaiting slot entry', max_length=100),
        ),
        migrations.AlterField(
            model_name='withdrawalrequest',
            name='status',
            field=models.CharField(choices=[('Under review', 'Under review'), ('Processing', 'Processing'), ('Failed', 'Failed'), ('Approved', 'Approved')], default='Checking', max_length=30),
        ),
        migrations.CreateModel(
            name='BalanceTracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_deposit', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('last_profits', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('last_bonus', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('time_updated', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('withdrawal_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='balance_tracker', to='app.withdrawalrequest')),
            ],
        ),
    ]
