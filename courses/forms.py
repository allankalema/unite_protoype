from django import forms

from .models import Course, Lesson, Module, Question, Quiz


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "slug",
            "short_description",
            "description",
            "cover_image",
            "is_published",
            "passing_score",
            "estimated_duration_hours",
        ]


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["course", "title", "order", "description"]


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "module",
            "title",
            "order",
            "content",
            "summary",
            "video_url",
            "downloadable_material_url",
        ]


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["course", "title", "description", "is_active"]


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["quiz", "text", "option_a", "option_b", "option_c", "option_d", "correct_option"]
