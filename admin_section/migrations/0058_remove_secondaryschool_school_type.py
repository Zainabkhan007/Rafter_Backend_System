# Generated by Django 5.1.4 on 2024-12-25 22:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0057_secondaryschool_school_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='secondaryschool',
            name='school_type',
        ),
    ]
