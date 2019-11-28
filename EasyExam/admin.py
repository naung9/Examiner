from django.contrib import admin
from . import models
from django import forms


# Register your models here.
class QuestionForm(forms.ModelForm):
    class Meta:
        models = models.Question
        fields = "__all__"
        widgets = {
            'question_text' : forms.Textarea(attrs={'rows': 3, 'cols': 45}),
            'question_image': forms.FileInput(attrs={'accept': 'image/*'}),
            'question_video': forms.FileInput(attrs={'accept': 'video/*'}),
            'question_audio': forms.FileInput(attrs={'accept': 'audio/*'}),
        }


class AdminQuestions(admin.TabularInline):
    model = models.Question
    form = QuestionForm
    extra = 0


class AdminExam(admin.ModelAdmin):
    inlines = (AdminQuestions,)


class AdminExamInline(admin.TabularInline):
    model = models.Exam
    extra = 0


class AdminExamGroup(admin.ModelAdmin):
    inlines = [AdminExamInline]


class AdminQuestion(admin.ModelAdmin):
    form = QuestionForm


admin.site.register(models.ExamGroup, AdminExamGroup)
admin.site.register(models.Exam, AdminExam)
admin.site.register(models.Question, AdminQuestion)
admin.site.register(models.Examinee)