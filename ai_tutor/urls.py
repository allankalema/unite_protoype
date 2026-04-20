from django.urls import path

from . import views

app_name = "ai_tutor"

urlpatterns = [
    path("ai/chat/", views.ai_chat_view, name="chat"),
    path("ai/chat/send/", views.ai_send_message_view, name="send"),
    path("ai/chat/<int:session_id>/clear/", views.clear_session_view, name="clear"),
    path("ai/history/", views.chat_history_view, name="history"),
]
