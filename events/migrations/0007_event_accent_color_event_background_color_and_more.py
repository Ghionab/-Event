# Generated migration to add accent_color and background_color to Event model

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('events', '0006_merge_0005_alter_event_status_0005_event_views_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='accent_color',
            field=models.CharField(blank=True, default='#10b981', max_length=7),
        ),
        migrations.AddField(
            model_name='event',
            name='background_color',
            field=models.CharField(blank=True, default='#f9fafb', max_length=7),
        ),
        migrations.AlterField(
            model_name='event',
            name='primary_color',
            field=models.CharField(blank=True, default='#4f46e5', max_length=7),
        ),
        migrations.AlterField(
            model_name='event',
            name='secondary_color',
            field=models.CharField(blank=True, default='#6b7280', max_length=7),
        ),
    ]
