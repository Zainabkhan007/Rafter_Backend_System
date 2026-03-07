from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0106_parentregisteration_platform_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='content',
        ),
        migrations.AddField(
            model_name='document',
            name='pdf_file',
            field=models.FileField(blank=True, null=True, upload_to='documents/'),
        ),
    ]
