# Generated by Django 3.2.14 on 2022-08-10 02:21

import api.models.app
import api.models.certificate
import api.models.key
import api.utils
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.BigIntegerField(primary_key=True, serialize=False, verbose_name='id')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='App',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('id', models.SlugField(max_length=63, null=True, unique=True, validators=[api.models.app.validate_app_id, api.models.app.validate_reserved_names])),
                ('structure', models.JSONField(blank=True, default=dict, validators=[api.models.app.validate_app_structure])),
                ('procfile_structure', models.JSONField(blank=True, default=dict, validators=[api.models.app.validate_app_structure])),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Application',
                'ordering': ['id'],
                'permissions': (('use_app', 'Can use app'),),
            },
        ),
        migrations.CreateModel(
            name='Build',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('image', models.TextField()),
                ('stack', models.CharField(max_length=32)),
                ('sha', models.CharField(blank=True, max_length=40)),
                ('procfile', models.JSONField(blank=True, default=dict)),
                ('dockerfile', models.TextField(blank=True)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'uuid')},
            },
        ),
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=253, unique=True, validators=[api.utils.validate_label])),
                ('certificate', models.TextField(validators=[api.models.certificate.validate_certificate])),
                ('key', models.TextField(validators=[api.models.certificate.validate_private_key])),
                ('common_name', models.TextField(editable=False, null=True)),
                ('san', models.JSONField(default=None, null=True)),
                ('fingerprint', models.CharField(editable=False, max_length=96)),
                ('expires', models.DateTimeField(editable=False)),
                ('starts', models.DateTimeField(editable=False)),
                ('issuer', models.TextField(editable=False)),
                ('subject', models.TextField(editable=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name', 'common_name', 'expires'],
            },
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('values', models.JSONField(blank=True, default=dict)),
                ('memory', models.JSONField(blank=True, default=dict)),
                ('lifecycle_post_start', models.JSONField(blank=True, default=dict)),
                ('lifecycle_pre_stop', models.JSONField(blank=True, default=dict)),
                ('cpu', models.JSONField(blank=True, default=dict)),
                ('tags', models.JSONField(blank=True, default=dict)),
                ('registry', models.JSONField(blank=True, default=dict)),
                ('healthcheck', models.JSONField(blank=True, default=dict)),
                ('termination_grace_period', models.JSONField(blank=True, default=dict)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'uuid')},
            },
        ),
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('domain', models.TextField(error_messages={'unique': 'Domain is already in use by another application'}, unique=True)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('certificate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.certificate')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['domain', 'certificate'],
            },
        ),
        migrations.CreateModel(
            name='Blocklist',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('id', models.CharField(db_index=True, max_length=128)),
                ('type', models.PositiveIntegerField(choices=[(1, 'app'), (2, 'user')])),
                ('remark', models.TextField(blank=True, default='Blocked for unknown reason', null=True)),
            ],
            options={
                'ordering': ['-created'],
                'unique_together': {('id', 'type')},
            },
        ),
        migrations.CreateModel(
            name='Volume',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=63, validators=[api.utils.validate_label])),
                ('size', models.CharField(max_length=128)),
                ('path', models.JSONField(blank=True, default=dict)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'name')},
            },
        ),
        migrations.CreateModel(
            name='TLS',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('https_enforced', models.BooleanField(null=True)),
                ('certs_auto_enabled', models.BooleanField(null=True)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'uuid')},
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('procfile_type', models.TextField()),
                ('path_pattern', models.TextField()),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'procfile_type')},
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=63, validators=[api.utils.validate_label])),
                ('plan', models.CharField(max_length=128)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('status', models.TextField(blank=True, null=True)),
                ('binding', models.TextField(blank=True, null=True)),
                ('options', models.JSONField(blank=True, default=dict)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('version', models.PositiveIntegerField()),
                ('summary', models.TextField(blank=True, null=True)),
                ('failed', models.BooleanField(default=False)),
                ('exception', models.TextField(blank=True, null=True)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('build', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.build')),
                ('config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.config')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'version')},
            },
        ),
        migrations.CreateModel(
            name='Key',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('id', models.CharField(max_length=128, unique=True)),
                ('public', models.TextField(error_messages={'unique': 'Public Key is already in use'}, unique=True, validators=[api.models.key.validate_base64])),
                ('fingerprint', models.CharField(editable=False, max_length=128)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'SSH Key',
                'ordering': ['public'],
                'unique_together': {('owner', 'fingerprint')},
            },
        ),
        migrations.CreateModel(
            name='AppSettings',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='UUID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('routable', models.BooleanField(null=True)),
                ('allowlist', models.JSONField(default=None, null=True)),
                ('autoscale', models.JSONField(blank=True, default=dict)),
                ('label', models.JSONField(blank=True, default=dict)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.app')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
                'unique_together': {('app', 'uuid')},
            },
        ),
    ]
