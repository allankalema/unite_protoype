from django import forms

from .models import Course, Lesson, LessonResource, Module, Question, Quiz


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "slug",
            "category",
            "level",
            "short_description",
            "description",
            "learning_objectives",
            "prerequisites",
            "target_audience",
            "created_by",
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
            "lesson_type",
            "duration_minutes",
            "content",
            "summary",
            "ai_summary",
            "ai_keywords",
            "video_url",
            "downloadable_material_url",
        ]


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["course", "title", "description", "is_active", "max_attempts"]


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["quiz", "text", "option_a", "option_b", "option_c", "option_d", "correct_option", "explanation"]


class LessonResourceForm(forms.ModelForm):
    class Meta:
        model = LessonResource
        fields = ["lesson", "title", "file_url", "resource_type"]
