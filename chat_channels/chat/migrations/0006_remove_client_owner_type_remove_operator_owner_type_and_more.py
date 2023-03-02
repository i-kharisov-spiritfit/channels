# Generated by Django 4.1.7 on 2023-02-15 23:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_client_owner_type_operator_owner_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='owner_type',
        ),
        migrations.RemoveField(
            model_name='operator',
            name='owner_type',
        ),
        migrations.AddField(
            model_name='chatmember',
            name='owner_type',
            field=models.CharField(default='unknown', max_length=10),
        ),
    ]