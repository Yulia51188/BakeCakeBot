# Generated by Django 3.2.8 on 2021-10-22 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bake_cake_bot', '0009_auto_20211021_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='choice_order',
            field=models.IntegerField(default=100000, verbose_name='Порядок выбора опций категории'),
        ),
    ]
