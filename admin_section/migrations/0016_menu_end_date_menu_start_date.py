# Generated by Django 5.1.4 on 2024-12-14 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0015_alter_menu_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='menu',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='menu',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]