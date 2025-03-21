# Generated by Django 5.1.7 on 2025-03-18 18:40

import django.db.models.deletion
import django_countries.fields
import phonenumber_field.modelfields
import timezone_field.fields
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_line_1', models.CharField(max_length=255)),
                ('address_line_2', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(max_length=255)),
                ('state', models.CharField(max_length=255)),
                ('zip_code', models.CharField(max_length=255)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('address_type', models.CharField(choices=[('Billing', 'Billing'), ('Shipping', 'Shipping'), ('Office', 'Office')], default='Office', max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Org Addresses',
                'db_table': 'Org_Address',
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=64, unique=True)),
                ('name_space', models.CharField(max_length=70, unique=True)),
                ('organization_type', models.CharField(choices=[('Enterprise', 'Enterprise'), ('Solo', 'Solo'), ('Team', 'Team')], default='Solo', max_length=10)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('tax_id', models.CharField(blank=True, max_length=255, null=True)),
                ('industry', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('logo_url', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='organization', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Organizations',
                'db_table': 'Organization',
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marketing_email', models.BooleanField(default=True)),
                ('security_email', models.BooleanField(default=True)),
                ('communication_email', models.BooleanField(default=True)),
                ('social_email', models.BooleanField(default=True)),
                ('sms_notifications', models.BooleanField(default=True)),
                ('push_notifications', models.BooleanField(default=True)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to='org.organization')),
            ],
            options={
                'verbose_name_plural': 'Notifications',
                'db_table': 'Org_Notification',
            },
        ),
        migrations.CreateModel(
            name='NotificationAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('invitation_sent', 'Invitation Sent'), ('member_deleted', 'Member Deleted'), ('profile_edited', 'Profile Edited'), ('role_changed', 'Role Changed'), ('payment_updated', 'Payment Method Updated'), ('settings_changed', 'Settings Changed')], max_length=30)),
                ('alert_message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_alerts', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_alerts', to='org.organization')),
            ],
            options={
                'verbose_name_plural': 'Org Notification Alerts',
                'db_table': 'Org_Notification_Alert',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InvoiceConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_to_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('language', models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('ht', 'Kreyol')], default='en', max_length=20)),
                ('purchase_order_number', models.CharField(blank=True, max_length=255, null=True)),
                ('billing_address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invoice_configs', to='org.address')),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='invoice_configs', to='org.organization')),
            ],
            options={
                'verbose_name_plural': 'Invoice Configs',
                'db_table': 'Org_Invoice_Config',
            },
        ),
        migrations.AddField(
            model_name='address',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='org.organization'),
        ),
        migrations.CreateModel(
            name='OrganizationMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')], default='INACTIVE', max_length=20)),
                ('joined_at', models.DateTimeField(blank=True, null=True)),
                ('is_owner', models.BooleanField(default=False)),
                ('is_admin', models.BooleanField(default=False)),
                ('last_active_at', models.DateTimeField(blank=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='org.organization')),
                ('permissions', models.ManyToManyField(blank=True, related_name='members', to='core.permission')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Members',
                'db_table': 'Org_Member',
            },
        ),
        migrations.CreateModel(
            name='OrganizationMemberInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('message', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10)),
                ('invited_at', models.DateTimeField(auto_now_add=True)),
                ('is_updated', models.BooleanField(default=False, editable=False)),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='org.organization')),
            ],
            options={
                'verbose_name_plural': 'Member Invitations',
                'db_table': 'Org_Member_Invitation',
            },
        ),
        migrations.CreateModel(
            name='OrganizationPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.CharField(choices=[('dark', 'Dark'), ('light', 'Light'), ('system', 'System')], default='system', max_length=6)),
                ('timezone', timezone_field.fields.TimeZoneField(default='UTC')),
                ('language', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='core.language')),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='org.organization')),
            ],
            options={
                'verbose_name_plural': 'Preferences',
                'db_table': 'Org_Preference',
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method_type', models.CharField(choices=[('Card', 'Card'), ('PayPal', 'PayPal'), ('Bank Transfer', 'Bank Transfer')], default='Card', max_length=50)),
                ('token_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('card_brand', models.CharField(blank=True, max_length=50, null=True)),
                ('card_last4', models.CharField(blank=True, max_length=4, null=True)),
                ('card_holder_name', models.CharField(blank=True, max_length=255, null=True)),
                ('card_expiration_month', models.IntegerField(blank=True, null=True)),
                ('card_expiration_year', models.IntegerField(blank=True, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('paypal_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('bank_account_last4', models.CharField(blank=True, max_length=4, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_method_options', to='org.organization')),
            ],
            options={
                'db_table': 'Org_Payment_Method',
            },
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_type', models.CharField(choices=[('free', 'Free'), ('basic', 'Basic'), ('premium', 'Premium'), ('enterprise', 'Enterprise')], default='free', max_length=20)),
                ('billing_cycle', models.CharField(choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly', max_length=10)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('start_date', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('auto_renew', models.BooleanField(default=True)),
                ('features', models.JSONField(blank=True, default=dict, help_text='Features included in this plan')),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='org.organization')),
            ],
            options={
                'verbose_name_plural': 'Org Subscriptions',
                'db_table': 'Org_Subscription',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('payment_method', models.CharField(choices=[('credit_card', 'Credit Card'), ('bank_transfer', 'Bank Transfer'), ('paypal', 'PayPal'), ('stripe', 'Stripe')], max_length=20)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='pending', max_length=10)),
                ('transaction_id', models.CharField(blank=True, max_length=255, null=True)),
                ('invoice_number', models.CharField(max_length=50, unique=True)),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('billing_period_start', models.DateField()),
                ('billing_period_end', models.DateField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='org.organization')),
                ('subscription', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='org.subscriptionplan')),
            ],
            options={
                'verbose_name_plural': 'Org Payments',
                'db_table': 'Org_Payment',
                'ordering': ['-payment_date'],
            },
        ),
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(fields=['name'], name='Organizatio_name_80f4d3_idx'),
        ),
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(fields=['email'], name='Organizatio_email_3055d3_idx'),
        ),
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(fields=['phone'], name='Organizatio_phone_2b2614_idx'),
        ),
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(fields=['name_space'], name='Organizatio_name_sp_f2a667_idx'),
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(fields=('name', 'email', 'phone', 'name_space'), name='unique_info'),
        ),
        migrations.AddConstraint(
            model_name='address',
            constraint=models.UniqueConstraint(fields=('organization', 'address_type'), name='unique_address_per_organization'),
        ),
        migrations.AddIndex(
            model_name='organizationmember',
            index=models.Index(fields=['organization'], name='Org_Member_organiz_88dd19_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationmember',
            index=models.Index(fields=['user'], name='Org_Member_user_id_657941_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationmember',
            index=models.Index(fields=['status'], name='Org_Member_status_4b26fd_idx'),
        ),
        migrations.AddConstraint(
            model_name='organizationmember',
            constraint=models.UniqueConstraint(fields=('organization', 'user'), name='unique_user_per_organization'),
        ),
        migrations.AddIndex(
            model_name='organizationmemberinvitation',
            index=models.Index(fields=['organization'], name='Org_Member__organiz_678c37_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationmemberinvitation',
            index=models.Index(fields=['email'], name='Org_Member__email_ad7af8_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationmemberinvitation',
            index=models.Index(fields=['status'], name='Org_Member__status_1fc809_idx'),
        ),
        migrations.AddConstraint(
            model_name='organizationmemberinvitation',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'PENDING')), fields=('organization', 'email'), name='unique_pending_invitation_per_email'),
        ),
        migrations.AddConstraint(
            model_name='organizationmemberinvitation',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'ACCEPTED')), fields=('organization', 'email'), name='unique_accepted_invitation_per_email'),
        ),
        migrations.AddIndex(
            model_name='paymentmethod',
            index=models.Index(fields=['method_type'], name='Org_Payment_method__47262c_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentmethod',
            index=models.Index(fields=['token_id'], name='Org_Payment_token_i_8d2f18_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_status'], name='Org_Payment_payment_1a72c6_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_date'], name='Org_Payment_payment_bd1e3d_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['invoice_number'], name='Org_Payment_invoice_872180_idx'),
        ),
    ]
