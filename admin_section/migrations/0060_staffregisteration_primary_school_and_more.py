# Generated by Django 5.1.4 on 2024-12-30 16:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0059_alter_menu_is_active_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffregisteration',
            name='primary_school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_section.primaryschool'),
        ),
        migrations.AddField(
            model_name='staffregisteration',
            name='secondary_school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_section.secondaryschool'),
        ),
    ]
