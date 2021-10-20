# Generated by Django 3.2.8 on 2021-10-20 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bake_cake_bot', '0006_option'),
    ]

    operations = [
        migrations.CreateModel(
            name='Inscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=256, verbose_name='Текст надписи')),
                ('price', models.IntegerField(db_index=True, verbose_name='Цена')),
            ],
        ),
    ]
