from django.db import connection
from django.shortcuts import render, get_object_or_404, redirect
from artwork.models import Expertise, ExpertiseItem, Painting
from django.db.models import Q

def paintings_list(request):
    """Отображение списка картин."""
    painting_request_query = request.GET.get('painting_title', '').lower()
    draft_expertise = Expertise.objects.filter(user=request.user, status=1).first() if request.user.is_authenticated else None

    return render(request, 'paintings_list.html', {
        'data': {
            'paintings': Painting.objects.filter(title__icontains=painting_request_query),
            'painting_request_query': painting_request_query,
            'expertise_count': draft_expertise.items.count() if draft_expertise else 0,
            'expertise_id': draft_expertise.id if draft_expertise else None
        }
    })

def painting_detail(request, id):
    """Отображение страницы с подробным описанием картины."""
    painting = get_object_or_404(Painting, id=id)
    return render(request, 'painting_detail.html', {'painting': painting})

def view_expertise(request, expertise_id):
    """Отображение страницы с заявкой на экспертизу."""
    if not request.user.is_authenticated:
        return redirect('paintings_list')

    expertise = get_object_or_404(Expertise, id=expertise_id, user=request.user)

    if expertise.status == 3:
        return redirect('paintings_list')

    expertise_items = expertise.items.select_related('painting')

    painting_request_query = request.GET.get('author', '').lower()

    if painting_request_query:
        expertise_items = expertise_items.filter(painting__author__icontains=painting_request_query)

    return render(request, 'expertise_summary.html', {
        'data': {
            'expertise_id': expertise.id,
            
            'items': expertise_items,
            'painting_request_query': painting_request_query,
        }
    })

def add_to_expertise(request):
    """Добавление выбранной картины в корзину и создание заявки."""
    if request.method == "POST" and request.user.is_authenticated:
        painting_id = request.POST.get("add_to_expertise")
        if painting_id:
            painting = get_object_or_404(Painting, id=painting_id)
            draft_expertise, created = get_or_create_expertise(request.user)
            expertise_item, created = ExpertiseItem.objects.get_or_create(expertise=draft_expertise, painting=painting)
            return redirect('paintings_list')

    return redirect('paintings_list')

def delete_expertise(request, expertise_id):
    """Удаление заказа"""
    sql = "UPDATE expertise SET status = 3 WHERE id =%s"
    with connection.cursor() as cursor:
        cursor.execute(sql, (expertise_id,))
    return redirect('paintings_list')

def get_or_create_expertise(user):
    """Получение или создание черновика заказа для пользователя"""
    draft_expertise, created = Expertise.objects.get_or_create(user=user, status=1)
    return draft_expertise, created

def delete_expertise_item(request, expertise_id, item_id):
   
    if request.method == "POST":
        expertise_item = get_object_or_404(ExpertiseItem, id=item_id, expertise__id=expertise_id)
        expertise_item.delete()
        return redirect('view_expertise', expertise_id=expertise_id)

    return redirect('paintings_list')

