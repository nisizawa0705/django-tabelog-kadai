# 会員登録のメール認証に使用
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator

def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verification_url = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    full_url = f"{settings.DOMAIN_NAME}{verification_url}"
    
    subject = "メールアドレスの確認"
    message = render_to_string('email_verification.html', {
        'user': user,
        'verification_url': full_url,
    })
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])