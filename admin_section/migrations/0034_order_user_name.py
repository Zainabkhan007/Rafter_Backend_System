# Generated by Django 5.1.4 on 2024-12-20 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0033_alter_order_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='user_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
