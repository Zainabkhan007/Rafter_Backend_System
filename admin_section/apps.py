from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AdminSectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_section'

    def ready(self):
        """
        This function runs when Django starts, ensuring that:
        - The admin user exists and has the correct password.
        - Email configuration is set from environment variables.
        - Stripe API keys are loaded dynamically.
        """
        from django.contrib.auth import get_user_model  # ✅ Move import here

        User = get_user_model()  # ✅ Use Django's safe way to access User model

        self.ensure_admin_user(User)
        self.configure_email_settings()
        self.configure_stripe_settings()

    def ensure_admin_user(self, User):
        """Create or update the admin user using environment variables."""
        admin_username = "admin"  # Default username
        admin_email = getattr(settings, "DEFAULT_FROM_EMAIL", "admin@example.com")
        admin_password = getattr(settings, "ADMIN_PASSWORD", None)

        if not admin_password:
            logger.warning("❌ ADMIN_PASSWORD is not set in environment variables!")
            return

        try:
            admin_user, created = User.objects.get_or_create(username=admin_username, defaults={'email': admin_email})
            
            if not admin_user.check_password(admin_password):
                admin_user.set_password(admin_password)
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.save()
                logger.info("✅ Admin password updated successfully!")

            else:
                logger.info("🔹 Admin password is already up-to-date.")

        except Exception as e:
            logger.error(f"❌ Error updating admin password: {str(e)}")

    def configure_email_settings(self):
        """Ensure email settings are correctly loaded from environment variables."""
        email_settings = {
            "EMAIL_PORT": getattr(settings, "EMAIL_PORT", None),
            "EMAIL_USE_TLS": getattr(settings, "EMAIL_USE_TLS", None),
            "EMAIL_HOST": getattr(settings, "EMAIL_HOST", None),
            "EMAIL_HOST_USER": getattr(settings, "EMAIL_HOST_USER", None),
            "EMAIL_HOST_PASSWORD": getattr(settings, "EMAIL_HOST_PASSWORD", None),
            "DEFAULT_FROM_EMAIL": getattr(settings, "DEFAULT_FROM_EMAIL", None),
            "MAIL_DEFAULT_SENDER": getattr(settings, "MAIL_DEFAULT_SENDER", None),
        }

        for key, value in email_settings.items():
            if not value:
                logger.warning(f"⚠️ {key} is not set in environment variables!")

        logger.info("✅ Email settings loaded successfully.")

    def configure_stripe_settings(self):
        """Ensure Stripe API keys are loaded from environment variables."""
        stripe_settings = {
            "STRIPE_PUBLIC_KEY": getattr(settings, "STRIPE_PUBLIC_KEY", None),
            "STRIPE_SECRET_KEY": getattr(settings, "STRIPE_SECRET_KEY", None),
        }

        for key, value in stripe_settings.items():
            if not value:
                logger.warning(f"⚠️ {key} is not set in environment variables!")

        logger.info("✅ Stripe settings loaded successfully.")