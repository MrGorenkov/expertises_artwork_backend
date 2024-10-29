from django.shortcuts import render, get_object_or_404, redirect
from artwork.models import Expertise, OrderItem, Painting
from django.contrib import messages

def paintings_list(request):
    """Отображение списка картин."""
    search_query = request.GET.get('painting_title', '').lower()

    # Получаем черновик заказа, если пользователь аутентифицирован
    draft_order = Expertise.objects.filter(user=request.user, status=1).first() if request.user.is_authenticated else None

    # Рендерим шаблон, передавая данные
    return render(request, 'paintings_list.html', {
        'data': {
            'paintings': Painting.objects.filter(title__icontains=search_query),
            'search_query': search_query,
            'order_count': draft_order.items.count() if draft_order else 0,  # Количество элементов
            'order_id': draft_order.id if draft_order else None
        }
    })

def painting_detail(request, id):
    """Отображение страницы с подробным описанием картины."""
    painting = get_object_or_404(Painting, id=id)
    return render(request, 'painting_detail.html', {'painting': painting})

def view_order(request, order_id):
    """Отображение страницы с заявкой на экспертизу."""
    if not request.user.is_authenticated:
        return redirect('paintings_list')  # Перенаправляем на список картин

    # Получаем заказ, проверяя статус
    order = get_object_or_404(Expertise, id=order_id, user=request.user)

    if order.status == 3:  # Статус "Удалено"
        return redirect('paintings_list')  # Или используйте HttpResponseNotFound

    order_items = order.items.select_related('painting')

    # Получаем значение поиска из GET-запроса
    search_query = request.GET.get('painting_title', '').lower()

    # Применяем фильтрацию по названию картины
    if search_query:
        order_items = order_items.filter(painting__title__icontains=search_query)

    return render(request, 'order_summary.html', {
        'data': {
            'order_id': order.id,
            
            'items': order_items,
            'search_query': search_query,  # Передаем значение поиска
        }
    })


def add_to_order(request):
    """Добавление выбранной картины в корзину и создание заявки."""
    if request.method == "POST" and request.user.is_authenticated:
        painting_id = request.POST.get("add_to_order")
        if painting_id:
            painting = get_object_or_404(Painting, id=painting_id)
            draft_order, created = get_or_create_order(request.user)
            OrderItem.objects.get_or_create(expertise=draft_order, painting=painting)

            # Добавляем сообщение об успешном добавлении
            messages.success(request, f'Картина "{painting.title}" была добавлена в корзину!')

    return redirect('paintings_list')

def delete_order(request, order_id):
    """Удаление заказа."""
    order = get_object_or_404(Expertise, id=order_id, user=request.user)  
    order.status = 3  # Устанавливаем статус "Удалено"
    order.save()
    return redirect('paintings_list')

def get_or_create_order(user):
    """Получение или создание черновика заказа для пользователя."""
    draft_order, created = Expertise.objects.get_or_create(user=user, status=1)
    return draft_order, created

def delete_order_item(request, order_id, item_id):
    """View to delete an item from the order."""
    if request.method == "POST":
        # Исправляем здесь: используем expertise__id вместо order__id
        order_item = get_object_or_404(OrderItem, id=item_id, expertise__id=order_id) 
        order_item.delete()  
        return redirect('view_order', order_id=order_id)  

    return redirect('paintings_list')