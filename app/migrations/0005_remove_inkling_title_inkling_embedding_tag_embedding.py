# Generated by Django 4.2.5 on 2023-10-04 03:31

from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_rename_text_inkling_content_inkling_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inkling',
            name='title',
        ),
        migrations.AddField(
            model_name='inkling',
            name='embedding',
            field=pgvector.django.VectorField(dimensions=768, null=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='embedding',
            field=pgvector.django.VectorField(dimensions=768, null=True),
        ),
    ]