# Generated by Django 4.2.4 on 2024-11-05 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artwork', '0003_alter_orderitem_expertise'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='author',
            field=models.CharField(blank=True, max_length=200, verbose_name='Автор'),
        ),
        migrations.AddField(
            model_name='painting',
            name='author',
            field=models.CharField(blank=True, max_length=200, verbose_name='Автор'),
        ),
    ]
