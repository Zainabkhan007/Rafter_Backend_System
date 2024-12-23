# Generated by Django 5.1.4 on 2024-12-22 21:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0043_alter_primarystudent_parent_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='primarystudent',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_parent', to='admin_section.parentregisteration'),
        ),
    ]