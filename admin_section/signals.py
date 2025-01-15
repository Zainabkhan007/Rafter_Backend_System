
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django_rest_passwordreset.signals import reset_password_token_created


def send_password_reset_email(user):
    """
    Sends a password reset email with the token for the newly registered user.
    """
    try:
        # Generate token for password reset
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Construct the reset URL
        reset_url = reverse('password_reset:reset-password-confirm')
        reset_url = f"{reset_url}?token={token}&uid={uid}"

        # Prepare email context
        context = {
            'username': user.username,
            'reset_password_url': reset_url,
            'reset_password_token': token,
        }

        # Render the plain text email and the HTML email
        email_plaintext_message = render_to_string('email/password_reset_email.txt', context)
        email_html_message = render_to_string('email/password_reset_email.html', context)

        # Send the email
        msg = EmailMultiAlternatives(
            subject="Password Reset Request",
            body=email_plaintext_message,
            from_email="testingsites247365@gmail.com",  # Replace with actual "from" email
            to=[user.email]
        )
        msg.attach_alternative(email_html_message, "text/html")
        msg.send()
    except Exception as e:
        print(f"[ERROR] Failed to send password reset email: {e}")
        raise