from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", views.dashboard_home_view, name="home"),
    path("dashboard/courses/", views.manage_courses_view, name="manage-courses"),
    path("dashboard/courses/create/", views.create_course_view, name="create-course"),
    path("dashboard/courses/<int:course_id>/edit/", views.edit_course_view, name="edit-course"),
    path("dashboard/courses/<int:course_id>/delete/", views.delete_course_view, name="delete-course"),
    path("dashboard/modules/", views.manage_modules_view, name="manage-modules"),
    path("dashboard/modules/create/", views.create_module_view, name="create-module"),
    path("dashboard/modules/<int:module_id>/edit/", views.edit_module_view, name="edit-module"),
    path("dashboard/modules/<int:module_id>/delete/", views.delete_module_view, name="delete-module"),
    path("dashboard/lessons/", views.manage_lessons_view, name="manage-lessons"),
    path("dashboard/lessons/create/", views.create_lesson_view, name="create-lesson"),
    path("dashboard/lessons/<int:lesson_id>/edit/", views.edit_lesson_view, name="edit-lesson"),
    path("dashboard/lessons/<int:lesson_id>/delete/", views.delete_lesson_view, name="delete-lesson"),
    path("dashboard/quizzes/", views.manage_quizzes_view, name="manage-quizzes"),
    path("dashboard/quizzes/create/", views.create_quiz_view, name="create-quiz"),
    path("dashboard/quizzes/<int:quiz_id>/edit/", views.edit_quiz_view, name="edit-quiz"),
    path("dashboard/quizzes/<int:quiz_id>/delete/", views.delete_quiz_view, name="delete-quiz"),
    path("dashboard/questions/create/<int:quiz_id>/", views.create_question_view, name="create-question"),
    path("dashboard/questions/<int:question_id>/edit/", views.edit_question_view, name="edit-question"),
    path("dashboard/questions/<int:question_id>/delete/", views.delete_question_view, name="delete-question"),
    path("dashboard/enrollments/", views.enrollment_list_view, name="enrollments"),
    path("dashboard/ai-logs/", views.ai_logs_view, name="ai-logs"),
]
