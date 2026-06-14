from django.urls import path

from . import views

app_name = 'trust'

urlpatterns = [
    path('verify-email/', views.verify_email_otp, name='verify-email'),
    path('verify-email/resend/', views.resend_email_otp, name='resend-email-otp'),
    path('safety/', views.safety_acknowledgement, name='safety'),
    path('student-id/', views.student_id_verification, name='student-id'),
    path('external-seller/', views.external_seller_application, name='external-seller'),
    path('report/<str:app_label>/<str:model_name>/<str:object_id>/', views.report_content, name='report-content'),
    path('transaction/request/<str:app_label>/<str:model_name>/<str:object_id>/', views.request_transaction, name='request-transaction'),
    path('transaction/<int:pk>/confirm/', views.confirm_transaction, name='confirm-transaction'),
    path('transaction/<int:pk>/dispute/', views.dispute_transaction, name='dispute-transaction'),
]
