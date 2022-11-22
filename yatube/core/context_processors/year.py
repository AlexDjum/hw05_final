import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    now = {'year': datetime.datetime.now().year}

    return now
