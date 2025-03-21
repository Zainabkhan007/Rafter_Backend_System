# Generated by Django 5.1.4 on 2024-12-22 21:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0045_alter_primarystudent_staff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='primarystudent',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student', to='admin_section.primaryschool'),
        ),
        migrations.AlterField(
            model_name='primarystudent',
            name='teacher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_teacher', to='admin_section.teacher'),
        ),
    ]
