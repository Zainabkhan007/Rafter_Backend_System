# Generated by Django 5.1.4 on 2024-12-22 17:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0039_class'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='class',
            name='student',
        ),
        migrations.RemoveField(
            model_name='class',
            name='teacher',
        ),
        migrations.RemoveField(
            model_name='student',
            name='school',
        ),
        migrations.RemoveField(
            model_name='student',
            name='teacher',
        ),
        migrations.CreateModel(
            name='PrimaryStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(default='', max_length=30)),
                ('last_name', models.CharField(default='', max_length=30)),
                ('username', models.CharField(default='', max_length=30)),
                ('student_email', models.EmailField(default='', max_length=254)),
                ('phone_no', models.IntegerField(blank=True, null=True)),
                ('password', models.CharField(default='', max_length=128)),
                ('class_year', models.CharField(default='', max_length=30)),
                ('parent', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='student_parent', to='admin_section.parentregisteration')),
                ('school', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='student', to='admin_section.primaryschool')),
                ('staff', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='student_staff', to='admin_section.staffregisteration')),
                ('teacher', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='student_teacher', to='admin_section.teacher')),
            ],
        ),
        migrations.AlterField(
            model_name='order',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='admin_section.primarystudent'),
        ),
        migrations.DeleteModel(
            name='StudentRegisteration',
        ),
        migrations.DeleteModel(
            name='Class',
        ),
        migrations.DeleteModel(
            name='Student',
        ),
    ]