# Generated by Django 5.1.4 on 2024-12-22 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0047_rename_student_email_primarystudent_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parentregisteration',
            name='allergies',
        ),
        migrations.AddField(
            model_name='parentregisteration',
            name='allergies',
            field=models.ManyToManyField(blank=True, to='admin_section.allergen'),
        ),
    ]
