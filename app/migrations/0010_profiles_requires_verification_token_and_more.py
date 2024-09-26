# Generated by Django 5.0.6 on 2024-08-27 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_is_verified_account_verified'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiles',
            name='requires_verification_token',
            field=models.BooleanField(default=False, help_text='Decide whether this user needs a verification token to submit account verification requests. If this is Turned on, this token will be automatically generated for this account but will not be mailed to them. You can decide to ask for certain payment to get this token from you. And if Turned off, the user will not be prompted for a verification token to submit account verification requests.', verbose_name='Verification Token'),
        ),
        migrations.AddField(
            model_name='profiles',
            name='verification_token',
            field=models.CharField(blank=True, editable=False, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='verification',
            name='facial',
            field=models.FileField(blank=True, null=True, upload_to='id_cards/videos/'),
        ),
        migrations.AddField(
            model_name='verification',
            name='nationality',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='verification',
            name='id_back',
            field=models.ImageField(blank=True, null=True, upload_to='id_cards/back'),
        ),
        migrations.AlterField(
            model_name='verification',
            name='id_front',
            field=models.ImageField(blank=True, null=True, upload_to='id_cards/front'),
        ),
    ]
