from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Email Management
    path('templates/', views.email_templates, name='email_templates'),
    path('templates/create/', views.email_template_create, name='email_template_create'),
    path('templates/<int:template_id>/edit/', views.email_template_edit, name='email_template_edit'),
    path('templates/<int:template_id>/delete/', views.email_template_delete, name='email_template_delete'),
    
    # Email Logs
    path('logs/', views.email_logs, name='email_logs'),
    
    # Scheduled Emails
    path('scheduled/', views.scheduled_emails, name='scheduled_emails'),
    path('scheduled/create/', views.scheduled_email_create, name='scheduled_email_create'),
    path('scheduled/<int:scheduled_id>/edit/', views.scheduled_email_edit, name='scheduled_email_edit'),
    path('scheduled/<int:scheduled_id>/delete/', views.scheduled_email_delete, name='scheduled_email_delete'),
    path('scheduled/<int:scheduled_id>/send/', views.send_scheduled_email, name='send_scheduled_email'),
    
    # Send Email
    path('send/', views.send_email, name='send_email'),
    
    # SMS Notifications
    path('sms/', views.sms_list, name='sms_list'),
    path('sms/send/', views.sms_send, name='sms_send'),
    
    # Push Notifications
    path('push/', views.push_list, name='push_list'),
    path('push/send/', views.push_send, name='push_send'),
    
    # Live Polls
    path('polls/', views.poll_list, name='poll_list'),
    path('polls/create/', views.poll_create, name='poll_create'),
    path('polls/<int:poll_id>/', views.poll_detail, name='poll_detail'),
    path('polls/<int:poll_id>/vote/', views.poll_vote, name='poll_vote'),
    path('polls/<int:poll_id>/close/', views.poll_close, name='poll_close'),
    path('polls/<int:poll_id>/results/', views.poll_results, name='poll_results'),
    
    # Live Q&A
    path('qa/', views.qa_list, name='qa_list'),
    path('qa/<int:event_id>/', views.qa_event, name='qa_event'),
    path('qa/<int:event_id>/ask/', views.qa_ask, name='qa_ask'),
    path('qa/<int:question_id>/upvote/', views.qa_upvote, name='qa_upvote'),
    path('qa/<int:question_id>/answer/', views.qa_answer, name='qa_answer'),
    path('qa/<int:question_id>/approve/', views.qa_approve, name='qa_approve'),
    
    # Reminders
    path('reminders/', views.reminder_list, name='reminder_list'),
    path('reminders/create/', views.reminder_create, name='reminder_create'),
    path('reminders/<int:reminder_id>/edit/', views.reminder_edit, name='reminder_edit'),
    path('reminders/<int:reminder_id>/delete/', views.reminder_delete, name='reminder_delete'),
]