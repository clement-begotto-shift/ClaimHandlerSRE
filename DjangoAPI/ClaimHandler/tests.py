from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Claim

class GetClaimTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('get-claim')

        # Create some initial claims in the database
        Claim.objects.create(Id=1, ClaimName="Claim1", Verified=True)
        Claim.objects.create(Id=2, ClaimName="Claim2", Verified=False)

    # Test to ensure non-GET methods are not allowed
    def test_invalid_method(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Test for a specific claim by ID
    def test_get_claim_by_id(self):
        response = self.client.get(self.url, {'Id': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['Id'], 2)

    # Test for a non-existing claim ID
    def test_get_claim_by_non_existing_id(self):
        response = self.client.get(self.url, {'Id': 100})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], "Claim with this ID does not exist")


class PostClaimTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('post-claims')

        # Create some initial claims in the database
        Claim.objects.create(Id=1, ClaimName="Claim1", Verified=True)
        Claim.objects.create(Id=2, ClaimName="Claim2", Verified=False)

    # Test to ensure non-POST methods are not allowed
    def test_invalid_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Test for handling malformed JSON
    def test_malformed_json(self):
        malformed_json = "[{Id: 7, ClaimName: InvalidJson"
        response = self.client.post(self.url, data=malformed_json, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('Malformed JSON body', response_data['error'])

    # Test for valid claims
    def test_add_only_existing_claims(self):
        self.valid_payload = [
            {"Id": 2, "ClaimName": "ValidClaim1", "Verified": True},
        ]
        response = self.client.post(self.url, data=self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertIn('All valid claims already exist', response_data['message'])
        self.assertIn('existing_ids', response_data)
        self.assertEqual(response_data['existing_ids'], [2])
        self.assertEqual(Claim.objects.count(), 2)  

    # Test for valid claims
    def test_add_valid_claims(self):
        self.valid_payload = [
            {"Id": 3, "ClaimName": "ValidClaim1", "Verified": True},
            {"Id": 4, "ClaimName": "ValidClaim2", "Verified": False},
        ]
        response = self.client.post(self.url, data=self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2 initial + 2 new claims
        self.assertEqual(Claim.objects.count(), 4)  

    # Test for invalid payloads (wrong types)
    def test_add_claim_with_invalid_id_types(self):
        self.invalid_payload_wrong_type = [
                {"Id": "six", "ClaimName": "ClaimInvalidIdType" }
            ]
        response = self.client.post(self.url, data=self.invalid_payload_wrong_type, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Some claims have malformed or no id', response_data['error'])
        self.assertEqual(response_data['index_with_missing_ids'], [0])

    # Test for claims with existing IDs
    def test_add_claim_with_existing_ids(self):
        self.payload_with_existing = [
            {"Id": 1, "ClaimName": "ExistingClaim", "Verified": True},
            {"Id": 5, "ClaimName": "NewClaim", "Verified": False}
        ]
        response = self.client.post(self.url, data=self.payload_with_existing, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertIn('existing_ids', response_data)
        self.assertEqual(response_data['existing_ids'], [1])

        # Only the new claim should be added
        # 2 initial + 1 new claim
        self.assertEqual(Claim.objects.count(), 3)

    # Test for invalid payloads (missing fields)
    def test_add_claim_with_missing_fields(self):
        self.invalid_payload_missing_fields = [
            {"Id": 6 }  # Missing 'ClaimName'
        ]
        response = self.client.post(self.url, data=self.invalid_payload_missing_fields, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertIn('ClaimName', response_data[0])
        self.assertEqual(len(response_data[0]['ClaimName']), 1)
        self.assertEqual(response_data[0]['ClaimName'][0], 'This field is required.')

    # Test for invalid payloads (wrong types)
    def test_add_claim_with_invalid_field_types(self):
        self.invalid_payload_wrong_type = [
                {"Id": 10, "ClaimName": "ClaimInvalidVerifiedType", "Verified": "XXX"}
            ]
        response = self.client.post(self.url, data=self.invalid_payload_wrong_type, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertIn('Verified', response_data[0])
        self.assertEqual(len(response_data[0]['Verified']), 1)
        self.assertEqual(response_data[0]['Verified'][0], 'Must be a valid boolean.')