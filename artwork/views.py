from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from artwork.models import Expertise, OrderItem, Painting
from django.db.models import Q

USER = 1

def paintings_list(request):
    """
    Отображение страницы со списком всех картин
    """
    # Получаем данные из строки поиска
    search_query = request.GET.get('painting_title', '').lower()

    # Получаем заявку пользователя в статусе черновик, если такая существует
    draft_order = Expertise.objects.filter(user=USER, status=Expertise.STATUS_CHOICES[0][0]).first()

    # Фильтруем картины по заголовку, начинающемуся с поискового запроса
    filtered_paintings = Painting.objects.filter(
        title__istartswith=search_query) 

    return render(request, 'paintings_list.html', {
        'data': {
            'paintings': filtered_paintings,
            'search_query': search_query,
            'order_count': draft_order.items.count() if draft_order else 0,
            'order_id': draft_order.id if draft_order else 0
        }
    })

def painting_detail(request, id):
    """
    Отображение страницы с подробным описанием выбранной картины
    """
    painting = get_object_or_404(Painting, id=id)
    return render(request, 'painting_detail.html', {'painting': painting})

def view_order(request, order_id):
    """
    Отображение страницы заявки на экспертизу
    """
    expertise_order = Expertise.objects.filter(
        ~Q(status=Expertise.STATUS_CHOICES[2][0]), id=order_id).first()

    if expertise_order is None:
        return redirect('paintings_list')

    order_items = OrderItem.objects.filter(order=expertise_order).select_related('painting')

    detailed_order = [
        {
            'id': item.painting.id,
            'title': item.painting.title,
            'img_path': item.painting.img_path
        }
        for item in order_items
    ]

    return render(request, 'order_summary.html', {
        'data': {
            'order_id': expertise_order.id,
            'items': detailed_order
        }
    })

def get_or_create_order(user_id):
    """
    Получение заявки или создание новой, если её нет
    """
    draft_order = Expertise.objects.filter(user_id=user_id, status=Expertise.STATUS_CHOICES[0][0]).first()

    if draft_order:
        return draft_order.id

    new_order = Expertise(user_id=user_id, status=Expertise.STATUS_CHOICES[0][0])
    new_order.save()
    return new_order.id

def add_to_order(request):
    """
    Добавление картины в заявку на экспертизу
    """
    if request.method != "POST":
        return redirect('paintings_list')

    painting_id = request.POST.get("add_to_order")

    if painting_id:
        order_id = get_or_create_order(USER)
        item = OrderItem(order_id=order_id, painting_id=painting_id)
        item.save()

    return paintings_list(request)

def delete_order(request, order_id):
    """
    Удаление заявки на экспертизу
    """
    sql = "UPDATE artwork_expertise SET status = %s WHERE id = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, (Expertise.STATUS_CHOICES[2][0], order_id))

    return redirect('paintings_list')

def delete_order_item(request, order_id):
    """
    Удаление картины из заявки на экспертизу
    """
    if request.method != "POST":
        return redirect('view_order', order_id=order_id)

    action = request.POST.get("action")

    if action == "delete_order":
        delete_order(request, order_id)
        return redirect('paintings_list')

    elif action.startswith("delete_item_"):
        item_id = action.split("_")[2]
        item = OrderItem.objects.get(id=item_id, order_id=order_id)
        item.delete()

    return view_order(request, order_id)
