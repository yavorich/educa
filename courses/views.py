from typing import Any, Optional
from django import http
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Course
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.detail import DetailView
from .forms import ModuleFormSet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.forms.models import modelform_factory, ModelForm
from django.apps import apps
from django.db.models import Model, Count
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from .models import Module, Content, Subject
from students.forms import CourseEnrollForm

# Create your views here.

class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin,
                       LoginRequiredMixin,
                       PermissionRequiredMixin):
    model = Course
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    '''
    Для преподавателей (настройка курсов)
    '''
    template_name = 'courses/manage/course/list.html'
    permission_required = 'courses.view_course'


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    permission_required = 'courses.delete_course'


class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None
    
    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course,
                             data=data)
    
    def dispatch(self, request: HttpRequest, pk: Any) -> HttpResponse:
        self.course = get_object_or_404(Course,
                                        id=pk,
                                        owner=request.user)
        return super().dispatch(request, pk)
    
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        formset = self.get_formset()
        return self.render_to_response({
            'course': self.course,
            'formset': formset
        })
    
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({
            'course': self.course,
            'formset': formset
        })


class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'
    
    def get_model(self, model_name: str) -> Optional[Model]:
        if model_name in ['text', 'image', 'video', 'file']:
            return apps.get_model(app_label='courses',
                                  model_name=model_name)
        return None
    
    def get_form(self, model, *args, **kwargs) -> ModelForm:
        Form = modelform_factory(model, exclude=['owner',
                                                 'order',
                                                 'created',
                                                 'updated'])
        return Form(*args, **kwargs)
    
    def dispatch(self, request: HttpRequest, module_id: Any, 
                 model_name: str, id: Any=None) -> HttpResponse:
        self.module = get_object_or_404(Module,
                                        id=module_id,
                                        course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model,
                                         id=id,
                                         owner=request.user)
        return super().dispatch(request, module_id, model_name, id)
    
    def get(self, request: HttpRequest, module_id: Any, 
            model_name: str, id: Any=None) -> HttpResponse:
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form,
                                        'object': self.obj})
    
    def post(self, request: HttpRequest, module_id: Any, 
             model_name: str, id: Any=None) -> HttpResponse:
        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # new content
                Content.objects.create(module=self.module,
                                       item=obj)
            return redirect('module_content_list', self.module.id)
        return self.render_to_response({'form': form,
                                        'object': self.obj})


class ContentDeleteView(View):
    def post(self, request: HttpRequest, id: Any) -> HttpResponse:
        content = get_object_or_404(Content,
                                    id=id,
                                    module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'
    
    def get(self, request: HttpRequest, module_id: Any) -> HttpResponse:
        module = get_object_or_404(Module,
                                   id=module_id,
                                   course__owner=request.user)
        return self.render_to_response({'module': module})


class ModuleOrderView(CsrfExemptMixin,
                      JsonRequestResponseMixin,
                      View):
    def post(self, request: HttpRequest) -> JsonResponse:
        for id, order in self.request_json.items():
            Module.objects.filter(
                id=id,
                course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentOrderView(CsrfExemptMixin,
                       JsonRequestResponseMixin,
                       View):
    def post(self, request: HttpRequest) -> JsonResponse:
        for id, order in self.request_json.items():
            Content.objects.filter(
                id=id,
                module__course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class CourseListView(TemplateResponseMixin, View):
    '''
    Для студентов (отображение курсов)
    '''
    model = Course
    template_name = 'courses/course/list.html'
    
    def get(self, request: HttpRequest, subject=None) -> HttpResponse:
        subjects = Subject.objects.annotate(total_courses=Count('courses'))
        courses = Course.objects.annotate(total_modules=Count('modules'))
        if subject:
            subject = get_object_or_404(Subject, slug=subject)
            courses = courses.filter(subject=subject)
        return self.render_to_response({'subjects': subjects,
                                        'subject': subject,
                                        'courses': courses})


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/detail.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        '''
        этот метод переопределяется для добавления аргументов
        в контекст прорисовки шаблона
        '''
        context = super().get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(
            initial={'course': self.object})
        return context
