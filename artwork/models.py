from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

# Модель для картин
class Painting(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название")
    img_path = models.CharField(max_length=255, verbose_name="Путь изображения")
    short_description = models.CharField(max_length=255, verbose_name="Краткое описание")
    description = models.TextField(verbose_name="Полное описание")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Картина"
        verbose_name_plural = "Картины"
        db_table = 'painting'


# Модель для заказов на экспертизу картин
class Expertise(models.Model):
    STATUS_CHOICES = (
        (1, 'Черновик'),
        (2, 'Сформировано'),
        (3, 'Удалено'),
        (4, 'Завершено'),
        (5, 'Отклонено'),
    )

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Пользователь", related_name="created_orders")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    manager = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Менеджер", related_name="managed_orders", blank=True, null=True)
    date_formation = models.DateTimeField(blank=True, null=True, verbose_name="Дата формирования")
    date_completion = models.DateTimeField(blank=True, null=True, verbose_name="Дата завершения")

    def __str__(self):
        return f"Заказ №{self.pk} от {self.user.username}"


    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        db_table = 'expertise'


# Модель для элементов в заказе
class OrderItem(models.Model):
    expertise = models.ForeignKey(Expertise, on_delete=models.DO_NOTHING, related_name="items", verbose_name="Заказ")
    painting = models.ForeignKey(Painting, on_delete=models.DO_NOTHING, verbose_name="Картина")
    comment = models.TextField(default="", blank=True, verbose_name="Комментарий")

    def __str__(self):
        return f"{self.painting.title} в заказе №{self.expertise.pk}"

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"
        db_table = 'order_item'
        unique_together = ('expertise', 'painting')
