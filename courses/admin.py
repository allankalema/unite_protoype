from django.contrib import admin

from .models import Course, Enrollment, Lesson, LessonProgress, LessonResource, Module, Question, Quiz, QuizAttempt


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "level", "created_by", "is_published", "passing_score", "estimated_duration_hours", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("is_published", "level", "category")
    search_fields = ("title", "short_description", "category")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "lesson_type", "duration_minutes", "order")
    list_filter = ("module", "lesson_type")


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
    list_display = ("title", "course", "is_active", "max_attempts")
    list_filter = ("is_active", "course")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "correct_option")


@admin.register(LessonResource)
class LessonResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "resource_type", "created_at")
    list_filter = ("resource_type",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "percentage", "passed", "attempted_at")
    list_filter = ("passed", "quiz")
