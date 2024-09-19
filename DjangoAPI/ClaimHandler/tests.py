from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Claim

class ClaimTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('post-claims')

        # Create some initial claims in the database
        Claim.objects.create(Id=1, ClaimName="TestClaim1", Verified=True)
        Claim.objects.create(Id=2, ClaimName="TestClaim2", Verified=False)

        # Valid payload for new claims
        self.valid_payload = [
            {"Id": 3, "ClaimName": "ValidClaim1", "Verified": True},
            {"Id": 4, "ClaimName": "ValidClaim2", "Verified": False},
        ]

        # Payload with some existing IDs
        self.payload_with_existing = [
            {"Id": 1, "ClaimName": "ExistingClaim", "Verified": True},  # Existing ID
            {"Id": 5, "ClaimName": "NewClaim", "Verified": False}       # New ID
        ]

        # Invalid payloads
        self.invalid_payload_missing_fields = [
            {"Id": 6, "ClaimName": "IncompleteClaim"}  # Missing 'Verified'
        ]

        self.invalid_payload_wrong_type = [
            {"Id": "six", "ClaimName": "InvalidClaim", "Verified": "yes"}  # Invalid types
        ]

    # Test for valid claims
    def test_add_valid_claims(self):
        response = self.client.post(self.url, data=self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Claim.objects.count(), 4)  # 2 initial + 2 new claims

    # Test for claims with existing IDs
    def test_add_claim_with_existing_ids(self):
        response = self.client.post(self.url, data=self.payload_with_existing, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertIn('existing_ids', response_data)
        self.assertEqual(response_data['existing_ids'], [1])

        # Only the new claim should be added
        self.assertEqual(Claim.objects.count(), 3)  # 2 initial + 1 new claim

    # Test for invalid payloads (missing fields)
    def test_add_claim_with_missing_fields(self):
        response = self.client.post(self.url, data=self.invalid_payload_missing_fields, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.json())

    # Test for invalid payloads (wrong types)
    def test_add_claim_with_invalid_field_types(self):
        response = self.client.post(self.url, data=self.invalid_payload_wrong_type, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.json())

    # Test for handling malformed JSON
    def test_malformed_json(self):
        malformed_json = "[{Id: 7, ClaimName: InvalidJson"
        response = self.client.post(self.url, data=malformed_json, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Malformed JSON body', response.json()['error'])

    # Test to ensure non-POST methods are not allowed
    def test_invalid_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)