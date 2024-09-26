from django.shortcuts import render

MINIO_HOST = '127.0.0.1'
MINIO_PORT = 9000
MINIO_DIR = 'web-img'

# Данные о картинах
paintings = [
    {
        'id': 0,
        'title': "Постоянство Памяти",
        'img_name': "memory.png",
        'artist': "Сальвадор Дали",
        'price': 83900,
        'short_description': "Известная картина Сальвадора Дали, изображающая плавящиеся часы.",
        'description': "Картина 'Постоянство памяти' (1931) Сальвадора Дали является одной из самых узнаваемых работ сюрреализма. Она изображает плавящиеся карманные часы в пейзаже, который символизирует относительность времени и нестабильность реальности."
    },
    {
        'id': 1,
        'title': "Крик",
        'img_name': "krik.png",
        'artist': "Эдвард Мунк",
        'price': 87900,
        'short_description': "Эмоциональная картина Эдварда Мунка, представляющая внутренние страхи и тревоги.",
        'description': "Картина 'Крик' (1893) Эдварда Мунка изображает фигуру на мосту с ужасающим криком, выражая человеческое состояние отчаяния и страха."
    },
    {
        'id': 2,
        'title': "Звездная ночь",
        'img_name': "starry_night.png",
        'artist': "Винсент Ван Гог",
        'price': 92900,
        'short_description': "Одна из самых известных картин Ван Гога, изображающая вихри ночного неба.",
        'description': "'Звездная ночь' (1889) — это шедевр Ван Гога, где он изображает завораживающее ночное небо, полное вихрей и светящихся звезд, создавая уникальное представление о природе."
    },
    {
        'id': 3,
        'title': "Афинская школа",
        'img_name': "school.png",
        'artist': "Рафаэль",
        'price': 71900,
        'short_description': "Фреска Рафаэля, изображающая знаменитых философов античности.",
        'description': "Фреска 'Афинская школа' (1511) Рафаэля изображает Платона и Аристотеля в центре, окруженных философами и учеными, представляя триумф разума и научной мысли."
    },
    {
        'id': 4,
        'title': "Ночной дозор",
        'img_name': "night.png",
        'artist': "Рембрандт",
        'price': 77900,
        'short_description': "Известная картина Рембрандта, изображающая вооруженную городскую милицию.",
        'description': "'Ночной дозор' (1642) — это шедевр Рембрандта, который изображает членов амстердамской стрелковой роты, подготовленных к выполнению своего долга. Картина выделяется своим драматизмом и светотеневым контрастом."
    },
    {
        'id': 5,
        'title': "Сотворение Адама",
        'img_name': "adam.png",
        'artist': "Микеланджело",
        'price': 103900,
        'short_description': "Фреска Микеланджело, изображающая момент создания человека.",
        'description': "'Сотворение Адама' (1512) — одна из фресок Сикстинской капеллы, изображающая библейскую сцену, где Бог протягивает руку к Адаму, даруя ему жизнь. Это один из самых узнаваемых образов в истории искусства."
    }
]


order_list = [
    {
        'id': 0,
        'title': "Постоянство Памяти",
        'img_name': "memory.png",
        'artist': "Сальвадор Дали",
        'price': 83900,
        'short_description': "Известная картина Сальвадора Дали, изображающая плавящиеся часы.",
        'description': "Картина 'Постоянство памяти' (1931) Сальвадора Дали является одной из самых узнаваемых работ сюрреализма. Она изображает плавящиеся карманные часы в пейзаже, который символизирует относительность времени и нестабильность реальности."
    },
    {
        'id': 1,
        'title': "Крик",
        'img_name': "krik.png",
        'artist': "Эдвард Мунк",
        'price': 87900,
        'short_description': "Эмоциональная картина Эдварда Мунка, представляющая внутренние страхи и тревоги.",
        'description': "Картина 'Крик' (1893) Эдварда Мунка изображает фигуру на мосту с ужасающим криком, выражая человеческое состояние отчаяния и страха."
    },
    {
        'id': 2,
        'title': "Звездная ночь",
        'img_name': "starry_night.png",
        'artist': "Винсент Ван Гог",
        'price': 92900,
        'short_description': "Одна из самых известных картин Ван Гога, изображающая вихри ночного неба.",
        'description': "'Звездная ночь' (1889) — это шедевр Ван Гога, где он изображает завораживающее ночное небо, полное вихрей и светящихся звезд, создавая уникальное представление о природе."
    }
]


def paintings_list(request):
    # Получаем данные из строки поиска
    search_query = request.GET.get('q', '').lower()
    # Фильтрация по названию или цене
    filtered_paintings = [
        painting for painting in paintings
        if search_query in painting['title'].lower() or search_query in str(painting['price'])
    ]
    # Формируем путь к изображениям для каждого элемента списка
    for painting in filtered_paintings:
        painting['img_path'] = f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/{painting["img_name"]}'
    
    # Рендерим шаблон с данными о картинах
    return render(request, 'paintings_list.html', {'data':{
        'paintings': filtered_paintings,
        'search_query': search_query,
        'order_count': len(order_list)
        }
    })

def painting_detail(request, id):
    # Детальная информация о картине
    for painting in paintings:
        if painting['id'] == id:
            painting['img_path'] = f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/{painting["img_name"]}'
            return render(request, 'painting_detail.html', {'painting': painting})

    return render(request, 'painting_detail.html')

def view_order(request):
    # Отображение содержимого заявки
    for painting in order_list:
        painting['img_path'] = f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/{painting["img_name"]}'
        print(f"Image path: {painting['img_path']}")  # Для отладки

    return render(request, 'order_summary.html', {'data': order_list})
