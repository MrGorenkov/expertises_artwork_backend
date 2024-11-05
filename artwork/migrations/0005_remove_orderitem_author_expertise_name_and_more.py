# Generated by Django 4.2.4 on 2024-11-05 22:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('artwork', '0004_orderitem_author_painting_author'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='author',
        ),
        migrations.AddField(
            model_name='expertise',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Название заявки'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='expertise',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='items', to='artwork.expertise', verbose_name='Заказ'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='painting',
            name='author',
            field=models.CharField(max_length=200, verbose_name='Автор'),
        ),
    ]
