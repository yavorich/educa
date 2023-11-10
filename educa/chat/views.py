from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def course_chat_room(request: HttpRequest, course_id) -> HttpResponse | HttpResponseForbidden:
    try:
        # извлечь курс с заданным id,
        # к которому присоединился текущий пользователь
        course = request.user.courses_joined.get(id=course_id)
    except:
        # пользователь не является студентом курса,
        # либо курс не существует
        return HttpResponseForbidden()
    return render(request, 'chat/room.html', {'course': course})
