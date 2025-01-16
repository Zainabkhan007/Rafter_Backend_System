from django.contrib.auth.tokens import PasswordResetTokenGenerator
# from django.utils import six

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        """
        Custom hash logic. 
        This is where you customize the hash value used in the reset link.
        """
        return f"{user.pk}{timestamp}{user.password}"