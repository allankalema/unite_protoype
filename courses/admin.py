from django.contrib import admin

from .models import Course, Enrollment, Lesson, LessonProgress, Module, Question, Quiz, QuizAttempt


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "passing_score", "estimated_duration_hours", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("is_published",)
    search_fields = ("title", "short_description")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order")
    list_filter = ("module",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "is_completed", "enrolled_at")
    list_filter = ("is_completed", "course")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "is_completed", "completed_at")
    list_filter = ("is_completed",)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "is_active")
    list_filter = ("is_active", "course")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "correct_option")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "percentage", "passed", "attempted_at")
    list_filter = ("passed", "quiz")
