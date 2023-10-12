# Generated by Django 4.2.5 on 2023-10-12 00:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import martor.models
import pgvector.django
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('app', '0002_add_vector_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='friends',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='intention',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='intention_embedding',
            field=pgvector.django.VectorField(dimensions=384, null=True),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('embedding', pgvector.django.VectorField(dimensions=384, null=True)),
                ('name', models.CharField(max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('user', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('privacy_setting', models.CharField(choices=[('private', 'Private'), ('friends', 'Friends'), ('friends_of_friends', 'Friends of Friends')], default='private', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('content', martor.models.MartorField()),
                ('summary', models.CharField(max_length=1024)),
                ('embedding', pgvector.django.VectorField(dimensions=384, null=True)),
                ('source_url', models.URLField(blank=True, max_length=2000, null=True)),
                ('source_name', models.CharField(blank=True, max_length=255, null=True)),
                ('publication_date', models.DateField(blank=True, null=True)),
                ('authors', models.CharField(blank=True, max_length=255, null=True)),
                ('tags', models.ManyToManyField(blank=True, to='app.tag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Memo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('privacy_setting', models.CharField(choices=[('private', 'Private'), ('friends', 'Friends'), ('friends_of_friends', 'Friends of Friends')], default='private', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('content', martor.models.MartorField()),
                ('summary', models.CharField(max_length=1024)),
                ('embedding', pgvector.django.VectorField(dimensions=384, null=True)),
                ('tags', models.ManyToManyField(blank=True, to='app.tag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LinkType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('reverse_name', models.CharField(default='', max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('user', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Inkling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('privacy_setting', models.CharField(choices=[('private', 'Private'), ('friends', 'Friends'), ('friends_of_friends', 'Friends of Friends')], default='private', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('content', martor.models.MartorField()),
                ('embedding', pgvector.django.VectorField(dimensions=384, null=True)),
                ('tags', models.ManyToManyField(blank=True, to='app.tag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(max_length=254)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending', max_length=10)),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('inviter', 'email')},
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('privacy_setting', models.CharField(choices=[('private', 'Private'), ('friends', 'Friends'), ('friends_of_friends', 'Friends of Friends')], default='private', max_length=20)),
                ('embedding', pgvector.django.VectorField(dimensions=384, null=True)),
                ('source_object_id', models.PositiveIntegerField()),
                ('target_object_id', models.PositiveIntegerField()),
                ('link_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.linktype')),
                ('source_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_links', to='contenttypes.contenttype')),
                ('tags', models.ManyToManyField(blank=True, to='app.tag')),
                ('target_content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_links', to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['link_type'],
                'unique_together': {('source_content_type', 'source_object_id', 'target_content_type', 'target_object_id', 'link_type')},
            },
        ),
        migrations.CreateModel(
            name='FriendRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_requests', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('sender', 'receiver')},
            },
        ),
    ]
