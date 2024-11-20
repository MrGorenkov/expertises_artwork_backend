# Generated by Django 4.2.4 on 2024-11-20 18:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('artwork', '0004_orderitem_author_painting_author'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpertiseItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.BooleanField(default=False, verbose_name='Результат проверки')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Комментарий')),
            ],
            options={
                'verbose_name': 'Элемент заказа',
                'verbose_name_plural': 'Элементы заказа',
                'db_table': 'expertise_item',
            },
        ),
        migrations.RemoveField(
            model_name='painting',
            name='author',
        ),
        migrations.AddField(
            model_name='expertise',
            name='author',
            field=models.CharField(blank=True, max_length=200, verbose_name='Автор'),
        ),
        migrations.AlterField(
            model_name='expertise',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='managed_expertises', to=settings.AUTH_USER_MODEL, verbose_name='Менеджер'),
        ),
        migrations.AlterField(
            model_name='expertise',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_expertises', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='painting',
            name='img_path',
            field=models.CharField(verbose_name='Путь изображения'),
        ),
        migrations.DeleteModel(
            name='OrderItem',
        ),
        migrations.AddField(
            model_name='expertiseitem',
            name='expertise',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='artwork.expertise', verbose_name='Заказ'),
        ),
        migrations.AddField(
            model_name='expertiseitem',
            name='painting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='artwork.painting', verbose_name='Картина'),
        ),
        migrations.AlterUniqueTogether(
            name='expertiseitem',
            unique_together={('expertise', 'painting')},
        ),
    ]
