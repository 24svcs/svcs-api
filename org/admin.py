from django.contrib import admin
from .models import Organization, OrganizationPreferences, Language, OrganizationMember, OrganizationMemberInvitation

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'name_space', 'email', 'phone', 'tax_id', 'logo_url')
    search_fields = ('id', 'name', 'name_space', 'email', 'phone', 'tax_id', 'logo_url')


@admin.register(OrganizationPreferences)
class OrganizationPreferencesAdmin(admin.ModelAdmin):
    list_display = ('id', 'theme', 'timezone')


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'language')
    search_fields = ('id', 'language')


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'organization', 'status')
    search_fields = ('id', 'user__email', 'organization__name')

