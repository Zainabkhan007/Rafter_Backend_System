# Generated by Django 5.1.4 on 2025-01-07 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0068_alter_parentregisteration_credits_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='primarystudentsregister',
            name='username',
            field=models.CharField(blank=True, max_length=60, null=True, unique=True),
        ),
    ]
