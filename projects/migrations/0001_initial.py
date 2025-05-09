# Generated by Django 4.1.3 on 2025-04-05 18:23

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('budget_min', models.DecimalField(decimal_places=2, max_digits=10)),
                ('budget_max', models.DecimalField(decimal_places=2, max_digits=10)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('job_type', models.CharField(choices=[('fixed', 'Fixed Price'), ('hourly', 'Hourly Rate')], default='fixed', max_length=10)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_jobs', to='users.profile')),
                ('freelancer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='freelancer_jobs', to='users.profile')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Milestone',
            fields=[
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('is_funded', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='projects.job')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('name', models.CharField(max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('featured_image', models.ImageField(blank=True, default='projects/default.jpg', null=True, upload_to='projects')),
                ('demo_link', models.CharField(blank=True, max_length=2000, null=True)),
                ('source_link', models.CharField(blank=True, max_length=2000, null=True)),
                ('vote_total', models.IntegerField(blank=True, default=0, null=True)),
                ('vote_ratio', models.IntegerField(blank=True, default=0, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
                ('tags', models.ManyToManyField(blank=True, to='projects.tag')),
            ],
            options={
                'ordering': ['-vote_ratio', '-vote_total', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('stripe_payment_id', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('escrow', 'In Escrow'), ('released', 'Released'), ('refunded', 'Refunded')], default='pending', max_length=10)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_payments', to='users.profile')),
                ('freelancer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='freelancer_payments', to='users.profile')),
                ('milestone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='projects.milestone')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.AddField(
            model_name='job',
            name='required_skills',
            field=models.ManyToManyField(blank=True, related_name='job_skills', to='projects.tag'),
        ),
        migrations.CreateModel(
            name='FreelancerReview',
            fields=[
                ('rating', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('comment', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_from_freelancers', to='users.profile')),
                ('freelancer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_as_freelancer', to='users.profile')),
                ('job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='freelancer_review', to='projects.job')),
            ],
        ),
        migrations.CreateModel(
            name='ClientReview',
            fields=[
                ('rating', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('comment', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_as_client', to='users.profile')),
                ('freelancer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews_from_clients', to='users.profile')),
                ('job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='client_review', to='projects.job')),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('body', models.TextField(blank=True, null=True)),
                ('value', models.CharField(choices=[('up', 'Up Vote'), ('down', 'Down Vote')], max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project')),
            ],
            options={
                'unique_together': {('owner', 'project')},
            },
        ),
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('delivery_time', models.IntegerField(help_text='Delivery time in days')),
                ('proposal', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('freelancer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='users.profile')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='projects.job')),
            ],
            options={
                'ordering': ['amount'],
                'unique_together': {('freelancer', 'job')},
            },
        ),
    ]
