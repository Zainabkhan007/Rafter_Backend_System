"""
Cron job functions for scheduled tasks.
This module is called by django-crontab.
"""
from django.core.management import call_command


def auto_complete_orders():
    """
    Auto-complete orders at 9pm daily.
    This function is called by the cron job defined in settings.py
    """
    call_command('auto_complete_orders')
