
# def validate_store_name(value, instance=None):
#     """
#     Validates a store name against various criteria:
#     - Uniqueness (no duplicate store names)
#     - Character set validation (allows letters, numbers, and appropriate punctuation)
#     - Length requirements (6-50 characters)
#     - Formatting rules (no excessive whitespace, no leading/trailing punctuation)
#     - Business suffix validation (requires meaningful content before suffixes)
#     - Prevention of generic-only names
    
#     Args:
#         value: The store name to validate
#         instance: Optional. When updating an existing store, this parameter
#                  should be the store instance being updated to exclude it
#                  from the uniqueness check. 
    
#     Returns:
#         The validated store name.
    
#     Raises:
#         ValidationError: If the store name fails any validation checks.
#     """ 
#     value = value.strip()
    
#     # Check for existing store with same name
#     query = Store.objects.filter(name__iexact=value)
#     if instance:
#         query = query.exclude(id=instance.id)
#     if query.exists():
#         raise serializers.ValidationError(_('A store with this name already exists.'))

#     # Basic character validation - expanded to include more valid punctuation and international characters
#     if not re.match(r'^[a-zA-Z0-9\s\.\&\-\'\,\(\)]+$', value):
#         raise serializers.ValidationError(_('Name can only contain letters, numbers, spaces, and basic punctuation (., &, -, \', (, )).'))
    
#     # Ensure name contains at least one letter
#     if not re.search(r'[a-zA-Z]', value):
#         raise serializers.ValidationError(_('Name must contain at least one letter.'))
    
#     # Length validation
#     if len(value) < 6:
#         raise serializers.ValidationError(_('Name must be at least 6 characters long.'))
#     if len(value) > 64:
#         raise serializers.ValidationError(_('Name cannot exceed 64 characters.'))

#     # Check for excessive whitespace
#     if re.search(r'\s{2,}', value):
#         raise serializers.ValidationError(_('Name cannot contain consecutive spaces.'))
    
#     # Check for consecutive punctuation
#     if re.search(r'[\.\&\-\'\,\(\)]{2,}', value):
#         raise serializers.ValidationError(_('Name cannot contain consecutive punctuation characters.'))
    
#     # Check for leading/trailing punctuation
#     if re.match(r'^[\.\&\-\'\,\(\)]', value) or re.search(r'[\.\&\-\'\,\(\)]$', value):
#         raise serializers.ValidationError(_('Name cannot start or end with punctuation.'))
    
#     # Check for common business terms at the end
#     common_suffixes = ['llc', 'inc', 'ltd', 'corporation', 'corp', 'company', 'co', 'sa', 'gmbh', 'ag', 'plc']
#     name_lower = value.lower()
#     for suffix in common_suffixes:
#         if name_lower.endswith(suffix) and (len(name_lower) == len(suffix) or name_lower[-len(suffix)-1] in [' ', '.', ',']):
#             # Validate that there's substantial content before the suffix
#             prefix = name_lower[:-len(suffix)].strip(' .,')
#             if len(prefix) < 3:
#                 raise serializers.ValidationError(_('Store name needs more content before the business suffix.'))
    
#     # Prevent names that are just generic terms
#     generic_terms = ['store', 'shop', 'business', 'enterprise', 'organization', 'corporation', 'consultancy', 'services']
#     if name_lower.strip() in generic_terms:
#         raise serializers.ValidationError(_('Store name cannot be a generic term.'))
    
#     return value
    
    


# def validate_store_name_space(value, instance=None):
#     """
#     Validates a store name space that will be used in URLs (e.g., domain.com/store-name-space).
    
#     Ensures the name space:
#     - Is unique across all stores
#     - Contains only URL-safe characters (letters, numbers, and hyphens)
#     - Has appropriate length (6-30 characters)
#     - Is not a reserved word that could conflict with system routes
#     - Contains at least one letter
    
#     Args:
#         value: The store name space to validate
#         instance: Optional. When updating an existing store, this parameter
#                  should be the store instance being updated to exclude it
#                  from the uniqueness check.
    
#     Returns:
#         The validated, lowercase store name space.
    
#     Raises:
#         ValidationError: If the store name space fails any validation checks.
#     """
#     value = value.lower().strip()
    
#     # Check for existing store with same name space
#     query = Store.objects.filter(name_space__iexact=value)
#     if instance:
#         query = query.exclude(id=instance.id)
#     if query.exists():
#         raise serializers.ValidationError(_('A store with this name space already exists.'))
    
#     # Character validation for URL safety - now including hyphens
#     if not re.match(r'^[a-z0-9\-]+$', value):
#         raise serializers.ValidationError(_('Name space can only contain lowercase letters, numbers, and hyphens with no spaces or other special characters.'))
    
#     # Ensure name space contains at least one letter
#     if not re.search(r'[a-z]', value):
#         raise serializers.ValidationError(_('Name space must contain at least one letter.'))
    
#     # Length validation
#     if len(value) < 6:
#         raise serializers.ValidationError(_('Name space must be at least 6 characters long.'))
#     if len(value) > 64:
#         raise serializers.ValidationError(_('Name space cannot exceed 64 characters.'))
    
#     # Check for reserved words that shouldn't be used in URLs
#     reserved_words = [
#         'admin', 'api', 'auth', 'login', 'logout', 'register', 
#         'dashboard', 'settings', 'profile', 'account', 'billing',
#         'help', 'support', 'about', 'terms', 'privacy', 'home',
#         'index', 'search', 'static', 'media', 'public', 'private',
#         'internal', 'external', 'system', 'default', 'test', 'demo'
#     ]
#     if value in reserved_words:
#         raise serializers.ValidationError(_('This name space is reserved and cannot be used.'))
    
#     # Check that it doesn't start with a number (good practice for identifiers)
#     if re.match(r'^[0-9]', value):
#         raise serializers.ValidationError(_('Name space should not start with a number.'))  
    
#     # Check for consecutive hyphens
#     if '--' in value:
#         raise serializers.ValidationError(_('Name space cannot contain consecutive hyphens.'))
    
#     # Check for leading/trailing hyphens
#     if value.startswith('-') or value.endswith('-'):
#         raise serializers.ValidationError(_('Name space cannot start or end with a hyphen.'))
    
#     return value

    