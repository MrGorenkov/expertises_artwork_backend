from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import random

class Painting(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название")
    img_path = models.TextField(verbose_name="Путь изображения")
    short_description = models.CharField(max_length=255, verbose_name="Краткое описание")
    description = models.TextField(verbose_name="Полное описание")
    
    
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Картина"
        verbose_name_plural = "Картины"
        db_table = 'painting'

class Expertise(models.Model):
    STATUS_CHOICES = (
        (1, 'Черновик'),
        (2, 'Сформировано'),
        (3, 'Удалено'),
        (4, 'Завершено'),
        (5, 'Отклонено'),
    )

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Пользователь", related_name="created_expertises")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    manager = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Менеджер", related_name="managed_expertises", blank=True, null=True)
    date_formation = models.DateTimeField(blank=True, null=True, verbose_name="Дата формирования")
    date_completion = models.DateTimeField(blank=True, null=True, verbose_name="Дата завершения")
    author = models.CharField(max_length=200, blank=True, verbose_name="Автор")
    result = models.BooleanField(default=False, verbose_name="Результат проверки")
    
    def __str__(self):
        return f"Заказ №{self.pk} от {self.user.username}"
    
    def save(self, *args, **kwargs):
        if self.status in [4, 5]:
            self.result = random.choice([True, False]) if self.status == 4 else False
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.items.all().delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        db_table = 'expertise'

class ExpertiseItem(models.Model):
    expertise = models.ForeignKey(Expertise, on_delete=models.SET_NULL, null=True, related_name="items", verbose_name="Заказ")
   
    painting = models.ForeignKey(Painting, on_delete=models.DO_NOTHING, verbose_name="Картина")
    comment = models.TextField(default="", blank=True, verbose_name="Комментарий") 

    def __str__(self):
        return f"{self.painting.title} в заказе №{self.expertise.pk if self.expertise else 'удален'}"

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"
        db_table = 'expertise_item'
        unique_together = ('expertise', 'painting')