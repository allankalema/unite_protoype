from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("courses/", views.course_list_view, name="list"),
    path("courses/<slug:slug>/", views.course_detail_view, name="detail"),
    path("courses/<slug:slug>/enroll/", views.enroll_course_view, name="enroll"),
    path("my-courses/", views.my_courses_view, name="my-courses"),
    path("learn/<slug:slug>/", views.course_learn_view, name="learn"),
    path("lessons/<int:lesson_id>/", views.lesson_detail_view, name="lesson-detail"),
    path("lessons/<int:lesson_id>/complete/", views.mark_lesson_complete_view, name="lesson-complete"),
    path("quizzes/<int:quiz_id>/", views.quiz_detail_view, name="quiz-detail"),
    path("quizzes/<int:quiz_id>/submit/", views.submit_quiz_view, name="quiz-submit"),
]
