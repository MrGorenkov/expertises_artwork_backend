from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from .models import Expertise, ExpertiseItem, Painting
from django.contrib.auth.models import User

# Создаем фиксированного пользователя для всех заявок
FIXED_USER = User.objects.get_or_create(username='fixed_user')[0]

def paintings_list(request):
    """Отображение списка картин."""
    title_query = request.GET.get('painting_title', '').lower()
    draft_expertise = Expertise.objects.filter(user=FIXED_USER, status=1).first()

    paintings = Painting.objects.all()
    if title_query:
        paintings = paintings.filter(title__icontains=title_query)

    return render(request, 'paintings_list.html', {
        'data': {
            'paintings': paintings,
            'painting_title_query': title_query,
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
    expertise = get_object_or_404(Expertise, id=expertise_id, user=FIXED_USER)
    
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'delete_expertise':
            expertise.status = 3  # Удалено
            expertise.save()
            return redirect('paintings_list')

    expertise_items = expertise.items.select_related('painting')

    return render(request, 'expertise_summary.html', {
        'data': {
            'expertise_id': expertise.id,
            'author': expertise.author,
            'items': expertise_items,
            'status': expertise.get_status_display(),
        }
    })

def add_to_expertise(request):
    """Добавление выбранной картины в корзину и создание заявки."""
    if request.method == "POST":
        painting_id = request.POST.get("add_to_expertise")
        if painting_id:
            painting = get_object_or_404(Painting, id=painting_id)
            draft_expertise, created = Expertise.objects.get_or_create(user=FIXED_USER, status=1)
            ExpertiseItem.objects.get_or_create(expertise=draft_expertise, painting=painting)
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



