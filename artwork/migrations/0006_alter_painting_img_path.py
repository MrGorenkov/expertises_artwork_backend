# Generated by Django 4.2.4 on 2024-11-20 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artwork', '0005_expertiseitem_remove_painting_author_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='painting',
            name='img_path',
            field=models.TextField(verbose_name='Путь изображения'),
        ),
    ]
