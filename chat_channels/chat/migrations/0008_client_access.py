# Generated by Django 4.1.7 on 2023-02-16 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_alter_operator_out_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='access',
            field=models.BooleanField(default=True, verbose_name='Доступен чат'),
        ),
    ]