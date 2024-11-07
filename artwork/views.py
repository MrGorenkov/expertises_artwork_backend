from django.db import connection
from django.shortcuts import render, get_object_or_404, redirect
from artwork.models import Expertise, OrderItem, Painting
from django.db.models import Q

def paintings_list(request):
    """Отображение списка картин."""
    search_query = request.GET.get('painting_title', '').lower()
    draft_order = Expertise.objects.filter(user=request.user, status=1).first() if request.user.is_authenticated else None

    return render(request, 'paintings_list.html', {
        'data': {
            'paintings': Painting.objects.filter(title__icontains=search_query),
            'search_query': search_query,
            'order_count': draft_order.items.count() if draft_order else 0,
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
        return redirect('paintings_list')

    order = get_object_or_404(Expertise, id=order_id, user=request.user)

    if order.status == 3:
        return redirect('paintings_list')

    order_items = order.items.select_related('painting')

    search_query = request.GET.get('author', '').lower()

    if search_query:
        order_items = order_items.filter(painting__author__icontains=search_query)

    return render(request, 'order_summary.html', {
        'data': {
            'order_id': order.id,
            
            'items': order_items,
            'search_query': search_query,
        }
    })

def add_to_order(request):
    """Добавление выбранной картины в корзину и создание заявки."""
    if request.method == "POST" and request.user.is_authenticated:
        painting_id = request.POST.get("add_to_order")
        if painting_id:
            painting = get_object_or_404(Painting, id=painting_id)
            draft_order, created = get_or_create_order(request.user)
            order_item, created = OrderItem.objects.get_or_create(expertise=draft_order, painting=painting)
            return redirect('paintings_list')

    return redirect('paintings_list')

def delete_order(request, order_id):
    """Удаление заказа"""
    sql = "UPDATE expertise SET status = 3 WHERE id =%s"
    with connection.cursor() as cursor:
        cursor.execute(sql, (order_id,))
    return redirect('paintings_list')

def get_or_create_order(user):
    """Получение или создание черновика заказа для пользователя"""
    draft_order, created = Expertise.objects.get_or_create(user=user, status=1)
    return draft_order, created

def delete_order_item(request, order_id, item_id):
   
    if request.method == "POST":
        order_item = get_object_or_404(OrderItem, id=item_id, expertise__id=order_id)
        order_item.delete()
        return redirect('view_order', order_id=order_id)

    return redirect('paintings_list')

