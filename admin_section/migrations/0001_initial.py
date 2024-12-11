# Generated by Django 5.1.3 on 2024-12-05 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PrimarySchool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_name', models.CharField(max_length=30)),
                ('school_email', models.EmailField(max_length=254)),
                ('school_eircode', models.CharField(max_length=30, unique=True)),
            ],
        ),
    ]
