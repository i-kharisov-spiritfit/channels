# Generated by Django 4.1.7 on 2023-04-07 12:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False, verbose_name='ID линии ')),
                ('name', models.CharField(default='Открытая линия Spirit. Fitness!', max_length=255, verbose_name='Название линии')),
                ('open', models.BooleanField(default=True, verbose_name='Открытый чат')),
            ],
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Имя')),
                ('surname', models.CharField(blank=True, max_length=255, null=True, verbose_name='Фамилия')),
                ('picture', models.CharField(blank=True, max_length=255, null=True, verbose_name='URL на аватарку')),
                ('chats', models.ManyToManyField(to='main.chat')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст сообщения')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Дата и время сообщения')),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.chat')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.member')),
            ],
        ),
        migrations.AddField(
            model_name='chat',
            name='line',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.line'),
        ),
        migrations.CreateModel(
            name='Access',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access', models.BooleanField(default=False, verbose_name='Есть доступ к линии')),
                ('line', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.line')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.member')),
            ],
        ),
    ]
