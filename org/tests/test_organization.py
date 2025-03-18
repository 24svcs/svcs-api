from rest_framework.test import APIClient
from rest_framework import status
import pytest
from django.contrib.auth import get_user_model

@pytest.mark.django_db
class TestCreateOrganization:
    def test_if_user_is_anonymous_returns_403(self):
        client = APIClient()
        response = client.post('/api/organizations/', {
            "name": "Test",
            "name_space": "test",
            "phone": "+201010101010",
            "email": "test@test.com",
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    

    def test_missing_required_values_returns_400(self):
        client = APIClient()
        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='testpass')
        client.force_authenticate(user=user)
        
        response = client.post('/api/organizations/', {
            "name_space": "testappfororganization",
            "phone": "+201010101010",
            "email": "test@test.com",
            "name": "testisthebest",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
