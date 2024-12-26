# Generated by Django 5.1.4 on 2024-12-25 21:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0055_alter_menu_end_date_alter_menu_start_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='admin_section.secondarystudent'),
        ),
        migrations.RemoveField(
            model_name='secondarystudent',
            name='seconadry_student_email',
        ),
        migrations.RemoveField(
            model_name='secondarystudent',
            name='secondary_class_year',
        ),
        migrations.RemoveField(
            model_name='secondarystudent',
            name='secondary_school',
        ),
        migrations.RemoveField(
            model_name='secondarystudent',
            name='secondary_student_name',
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='allergies',
            field=models.ManyToManyField(blank=True, null=True, to='admin_section.allergens'),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='class_year',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='email',
            field=models.EmailField(default='', max_length=254),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='first_name',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='last_name',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='password',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='phone_no',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student', to='admin_section.secondaryschool'),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='username',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.CreateModel(
            name='PrimaryStudentsRegister',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('class_year', models.CharField(max_length=30)),
                ('allergies', models.ManyToManyField(blank=True, null=True, to='admin_section.allergens')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_parent', to='admin_section.parentregisteration')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student', to='admin_section.primaryschool')),
                ('staff', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_staff', to='admin_section.staffregisteration')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_teacher', to='admin_section.teacher')),
            ],
        ),
        migrations.DeleteModel(
            name='PrimaryStudent',
        ),
    ]
