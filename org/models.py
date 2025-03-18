
from django.db import models
import uuid
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField
from timezone_field import TimeZoneField
from core.models import User, Permission, Language

# <========== Organization Manager ==========> #
class OrganizationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
class AllOrganizationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
    
    
# <========== Organization Model ==========> #
class Organization(models.Model):
    
    ENTERPRISE = 'Enterprise'
    SOLO = 'Solo'
    TEAM = 'Team'
    
    ORGANIZATION_TYPE_CHOICES = [
        (ENTERPRISE, 'Enterprise'),
        (SOLO, 'Solo'),
        (TEAM, 'Team'),
    ]
    
     # Member limits by organization type
    MEMBER_LIMITS = {
        SOLO: 1,
        TEAM: 20,
        ENTERPRISE: 50,
    }

    
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organization')
    name = models.CharField(max_length=64, unique=True)
    name_space = models.CharField(max_length=70, unique=True)
    organization_type = models.CharField(max_length=10, choices=ORGANIZATION_TYPE_CHOICES, default=SOLO)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(unique=True)
    description = models.TextField(blank=True, null=True)
    tax_id = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    objects = OrganizationManager()
    all_objects = AllOrganizationManager()
    
    class Meta:
        db_table = 'Organization'
        verbose_name_plural = "Organizations"
        
        indexes = [
            
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['name_space']),
        ]
        
        constraints = [
            models.UniqueConstraint(fields=['name', 'email', 'phone', 'name_space'], name='unique_info')
        ]
        
    
    def get_member_limit(self):
        """Return the maximum number of members allowed for this organization type."""
        return self.MEMBER_LIMITS.get(self.organization_type, 1)
    
    def can_add_member(self):
        """Check if the organization can add more members."""
        current_member_count = self.members.only('id').count()
        return current_member_count < self.get_member_limit()
    
    def get_available_members(self):
        """Return the number of available members for the organization."""
        return self.get_member_limit() - self.members.only('id').count()
        
    def __str__(self):
        return self.name
    
    def soft_delete(self):
        self.is_active = False
        self.save()
        
    def is_member(self, user):
        """Check if a user is a member of the organization."""
        return self.members.select_related('user').prefetch_related('members').filter(user=user, status=OrganizationMember.ACTIVE).exists()
        
    def is_admin(self, user):
        """Check if a user is an admin of the organization."""
        return self.members.select_related('user').prefetch_related('members').filter(user=user, status=OrganizationMember.ACTIVE, is_admin=True).exists()
        
        


class OrganizationMember(models.Model):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    
 
    MEMBER_STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    status = models.CharField(max_length=20, choices=MEMBER_STATUS_CHOICES, default=INACTIVE)
    permissions = models.ManyToManyField(Permission, related_name='members', blank=True)
    joined_at = models.DateTimeField(null=True, blank=True) #TODO: remove null=True, blank=True
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)   
    last_active_at = models.DateTimeField(null=True, blank=True) 
    
    class Meta:
        db_table = 'Org_Member'
        verbose_name_plural = "Members"
        constraints = [
            models.UniqueConstraint(fields=['organization', 'user'], name='unique_user_per_organization')
        ]
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user} (Organization: {self.organization.name})"
    
    
class OrganizationMemberInvitation(models.Model):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    
    INVITATION_STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=INVITATION_STATUS_CHOICES, default=PENDING)
    invited_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='+', null=True)
    is_updated = models.BooleanField(editable=False, default=False)
    
    class Meta:
        db_table = 'Org_Member_Invitation'
        verbose_name_plural = "Member Invitations"
        
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'email'],
                condition=models.Q(status="PENDING"),
                name='unique_pending_invitation_per_email'
            ),
            models.UniqueConstraint(
                fields=['organization', 'email'],
                condition=models.Q(status="ACCEPTED"),
                name='unique_accepted_invitation_per_email'
            )
        ]
        
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
        
    def __str__(self):
        return f"{self.email} (Organization: {self.organization.name})"


        
# <========== Address Model ==========> #
class Address(models.Model):
    BILLING = "Billing"
    SHIPPING = "Shipping"
    OFFICE = "Office"
    ADDRESS_CHOICES = [(BILLING, "Billing"), (SHIPPING, "Shipping"), (OFFICE, "Office")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='addresses')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255)
    country = CountryField()
    address_type = models.CharField(max_length=255, choices=ADDRESS_CHOICES, default=OFFICE)


    def __str__(self):
        return f"{self.organization.name} - {self.get_address_type_display()} Address"

    class Meta:
        db_table = 'Org_Address'
        verbose_name_plural = "Org Addresses"
        constraints = [
            models.UniqueConstraint(fields=['organization', 'address_type'], name='unique_address_per_organization')
        ]


# <========== Invoice Config Model ==========> #

class InvoiceConfig(models.Model):
    ENGLISH = 'en'
    SPANISH = 'es'
    FRENCH = 'fr'
    KREYOL = 'ht'
    
    INVOICING_LANGUAGE_CHOICES = [
        (ENGLISH, 'English'),
        (SPANISH, 'Spanish'),
        (FRENCH, 'French'),
        (KREYOL, 'Kreyol'),
    ]

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='invoice_configs')
    sent_to_email = models.EmailField(null=True, blank=True)
    billing_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='invoice_configs', null=True, blank=True)
    language = models.CharField(max_length=20, choices=INVOICING_LANGUAGE_CHOICES, default=ENGLISH)
    purchase_order_number = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.sent_to_email:
            self.sent_to_email = self.organization.email
        if not self.billing_address:
            billing_address = Address.objects.select_related('organization').filter(organization=self.organization, address_type=Address.BILLING).first()
            if not billing_address:
                billing_address = Address.objects.select_related('organization').filter(organization=self.organization, address_type=Address.OFFICE).first()
            self.billing_address = billing_address
        super().save(*args, **kwargs)

    def __str__(self):
        return f"InvoiceConfig for {self.organization.name}"
    
    class Meta:
        db_table = 'Org_Invoice_Config'
        verbose_name_plural = "Invoice Configs"




# <========== Notification Preference Model ==========> #
class NotificationPreference(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='notification_preferences')

    # Email Preferences
    marketing_email = models.BooleanField(default=True)
    security_email = models.BooleanField(default=True)
    communication_email = models.BooleanField(default=True)
    social_email = models.BooleanField(default=True)

    # Other Notifications
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification Preferences for {self.organization.name}"
    
    
    class Meta:
        db_table = 'Org_Notification'
        verbose_name_plural = "Notifications"
    


class NotificationAlert(models.Model):
    INVITATION_SENT = 'invitation_sent'
    MEMBER_DELETED = 'member_deleted'
    PROFILE_EDITED = 'profile_edited'
    ROLE_CHANGED = 'role_changed'
    PAYMENT_UPDATED = 'payment_updated'
    SETTINGS_CHANGED = 'settings_changed'
    
    ALERT_TYPE_CHOICES = [
        (INVITATION_SENT, 'Invitation Sent'),
        (MEMBER_DELETED, 'Member Deleted'),
        (PROFILE_EDITED, 'Profile Edited'),
        (ROLE_CHANGED, 'Role Changed'),
        (PAYMENT_UPDATED, 'Payment Method Updated'),
        (SETTINGS_CHANGED, 'Settings Changed'),
    ]
    

    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notification_alerts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    alert_message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_alert_type_display()} alert for {self.organization.name}"
    
    class Meta:
        db_table = 'Org_Notification_Alert'
        verbose_name_plural = "Org Notification Alerts"
        ordering = ['-created_at']


# <========== Preferences Model ==========> #
class OrganizationPreferences(models.Model):
    
    DARK = 'dark'
    LIGHT = 'light'
    SYSTEM = 'system'
    
    
    MODE_CHOICES = [
        (DARK, 'Dark'),
        (LIGHT, 'Light'),
        (SYSTEM, 'System')
    ]
    
    

    
    
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='preferences')
    theme  = models.CharField(max_length=6, choices=MODE_CHOICES, default=SYSTEM)
    language = models.OneToOneField(Language, on_delete=models.CASCADE, related_name='preferences')
    timezone = TimeZoneField(default='UTC')
    
    def __str__(self):
        return f"Preferences for {self.organization.name}"
    
    class Meta:
        db_table = 'Org_Preference'
        verbose_name_plural = "Preferences"


# <========== Subscription Plan Model ==========> #
class SubscriptionPlan(models.Model):
    FREE = 'free'
    BASIC = 'basic'
    PREMIUM = 'premium'
    ENTERPRISE = 'enterprise'
    
    PLAN_TYPE_CHOICES = [
        (FREE, 'Free'),
        (BASIC, 'Basic'),
        (PREMIUM, 'Premium'),
        (ENTERPRISE, 'Enterprise'),
    ]
    
    MONTHLY = 'monthly'
    YEARLY = 'yearly'
    
    BILLING_CYCLE_CHOICES = [
        (MONTHLY, 'Monthly'),
        (YEARLY, 'Yearly'),
    ]
    
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default=FREE)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES, default=MONTHLY)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    features = models.JSONField(default=dict, blank=True, help_text="Features included in this plan")
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_plan_type_display()} Plan"
    
    class Meta:
        db_table = 'Org_Subscription'
        verbose_name_plural = "Org Subscriptions"


# <========== Payment Model ==========> #
class Payment(models.Model):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    
    PAYMENT_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (REFUNDED, 'Refunded'),
    ]
    
    CREDIT_CARD = 'credit_card'
    BANK_TRANSFER = 'bank_transfer'
    PAYPAL = 'paypal'
    STRIPE = 'stripe'
    
    PAYMENT_METHOD_CHOICES = [
        (CREDIT_CARD, 'Credit Card'),
        (BANK_TRANSFER, 'Bank Transfer'),
        (PAYPAL, 'PayPal'),
        (STRIPE, 'Stripe'),
    ]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default=PENDING)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.organization.name} - {self.invoice_number}"
    
    class Meta:
        db_table = 'Org_Payment'
        verbose_name_plural = "Org Payments"
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_status']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['invoice_number']),
        ]
        

     
class PaymentMethod(models.Model):
    CARD = "Card"
    PAYPAL = "PayPal"
    BANK_TRANSFER = "Bank Transfer"
    
    PAYMENT_METHOD_CHOICES = [
        (CARD, "Card"),
        (PAYPAL, "PayPal"),
        (BANK_TRANSFER, "Bank Transfer"),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payment_method_options')
    method_type = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default=CARD)
    token_id = models.CharField(max_length=255, unique=True, blank=True, null=True) 
    card_brand = models.CharField(max_length=50, blank=True, null=True) 
    card_last4 = models.CharField(max_length=4, blank=True, null=True) 
    card_holder_name = models.CharField(max_length=255, blank=True, null=True)
    card_expiration_month = models.IntegerField(blank=True, null=True)
    card_expiration_year = models.IntegerField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    paypal_email = models.EmailField(blank=True, null=True)
    bank_account_last4 = models.CharField(max_length=4, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.method_type == self.CARD:
            return f"{self.card_brand} ending in {self.card_last4}"
        elif self.method_type == self.PAYPAL:
            return f"PayPal ({self.paypal_email})"
        elif self.method_type == self.BANK_TRANSFER:
            return f"Bank Transfer ending in {self.bank_account_last4}"
        return "Unknown Payment Method"

    class Meta:
        db_table = 'Org_Payment_Method'
        indexes = [
            models.Index(fields=["method_type"]),
            models.Index(fields=["token_id"]),
        ]
        
        
#todo in serializers
# from timezone_field.rest_framework import TimeZoneSerializerField