from rest_framework.response import Response
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import EmailMessage, get_connection, BadHeaderError
from templated_mail.mail import BaseEmailMessage

def send_email(request):

    subject = "Hello from Django SMTP"
    recipient_list = ["delivered@resend.dev"]
    from_email = "onboarding@resend.dev"
    message = "<strong>it works!</strong>"

    with get_connection(
        host=settings.RESEND_SMTP_HOST,
        port=settings.RESEND_SMTP_PORT,
        username=settings.RESEND_SMTP_USERNAME,
        password=settings.RESEND_API_KEY,
        use_tls=True,
        ) as connection:
            try:
                message = EmailMessage(
                    subject=subject,
                    body=message,
                    to=recipient_list,
                    from_email=from_email,
                    connection=connection)
                # message.attach_file(file_path)
                message.send()
            except BadHeaderError:
                return JsonResponse({"status": "error", "message": "Invalid header found."})
    return JsonResponse({"status": "ok"})