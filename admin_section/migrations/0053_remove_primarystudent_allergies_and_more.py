# Generated by Django 5.1.4 on 2024-12-23 12:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0052_alter_parentregisteration_allergies_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='primarystudent',
            name='allergies',
        ),
        migrations.AddField(
            model_name='primarystudent',
            name='allergies',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_section.allergens'),
        ),
    ]
