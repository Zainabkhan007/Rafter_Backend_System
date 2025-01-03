# Generated by Django 5.1.4 on 2025-01-02 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0063_order_primary_school_order_secondary_school'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.IntegerField(blank=True, null=True)),
                ('subject', models.CharField(max_length=30)),
                ('message', models.CharField(max_length=30)),
                ('photo_filename', models.CharField(max_length=30)),
            ],
        ),
    ]
