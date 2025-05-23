# Generated by Django 4.1.3 on 2025-04-05 19:47

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='client_rating',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
        migrations.AddField(
            model_name='profile',
            name='client_reviews_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='completion_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='profile',
            name='freelancer_rating',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
        migrations.AddField(
            model_name='profile',
            name='freelancer_reviews_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='hourly_rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='trust_score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='user_type',
            field=models.CharField(choices=[('both', 'Client & Freelancer'), ('client', 'Client Only'), ('freelancer', 'Freelancer Only')], default='both', max_length=20),
        ),
        migrations.AddField(
            model_name='skill',
            name='endorsements',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='skill',
            name='experience_level',
            field=models.IntegerField(default=1),
        ),
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('badge_type', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'), ('expert', 'Expert'), ('master', 'Master'), ('special', 'Special Achievement')], max_length=20)),
                ('image', models.ImageField(blank=True, null=True, upload_to='badges/')),
                ('requirements', models.JSONField(default=dict, help_text='JSON with badge requirements')),
                ('points', models.IntegerField(default=10, help_text='Points awarded for earning this badge')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('skill_related', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='badges', to='users.skill')),
            ],
        ),
        migrations.CreateModel(
            name='BadgeAssignment',
            fields=[
                ('date_earned', models.DateTimeField(auto_now_add=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('badge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.badge')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
            ],
            options={
                'unique_together': {('profile', 'badge')},
            },
        ),
    ]
