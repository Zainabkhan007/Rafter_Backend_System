# Generated by Django 5.1.4 on 2025-01-02 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0065_alter_contactmessage_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='parentregisteration',
            name='credits',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='secondarystudent',
            name='credits',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='staffregisteration',
            name='credits',
            field=models.IntegerField(default=0),
        ),
    ]
