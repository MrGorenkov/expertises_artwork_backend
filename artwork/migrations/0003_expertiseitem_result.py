# Generated by Django 4.2.4 on 2024-11-19 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artwork', '0002_remove_expertiseitem_author_remove_painting_author_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertiseitem',
            name='result',
            field=models.BooleanField(default=False, verbose_name='Результат проверки'),
        ),
    ]
