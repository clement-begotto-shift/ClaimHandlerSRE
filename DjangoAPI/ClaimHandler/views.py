from django.http import JsonResponse

from rest_framework.views import APIView

from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework import status

from .serializers import ClaimSerializer
from .models import Claim


class ClaimHandlerView(APIView):

    @api_view(['GET'])
    def get(request):
        claim_id = request.query_params.get('Id', None)

        # If an Id is provided in the query parameters
        if claim_id:
            try:
                claim = Claim.objects.get(Id=claim_id)
                serializer = ClaimSerializer(claim)
                return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
            except Claim.DoesNotExist:
                return JsonResponse({"error": "Claim with this ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        # If no Id is provided, return the top 5 claims ordered by Id
        else:
            claims = Claim.objects.all().order_by('Id')[:5]
            serializer = ClaimSerializer(claims, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

    @api_view(['POST'])
    def postClaims(request):
        if request.method != 'POST':
            return JsonResponse("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED, safe=False)

        try:
            # Parse the incoming request data
            claim_data = JSONParser().parse(request)
        except Exception as e:
            return JsonResponse({"error": "Malformed JSON body", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST, safe=False)

        # Check if the incoming data is a list
        if not isinstance(claim_data, list):
            return JsonResponse({"error": "Expected a list of claims"}, status=status.HTTP_400_BAD_REQUEST, safe=False)

        # List to collect any errors during the sanity checks
        errors = []
        
        # Sanity check each claim in the list
        required_fields = {'Id': int, 'ClaimName': str, 'Verified': bool}
        valid_claims = []

        for idx, claim in enumerate(claim_data):
            if not isinstance(claim, dict):
                errors.append({"index": idx, "error": "Each claim should be a dictionary"})
                continue

            missing_fields = [field for field in required_fields if field not in claim]
            if missing_fields:
                errors.append({"index": idx, "error": f"Missing required fields: {', '.join(missing_fields)}"})
                continue

            # Check if the field types are correct
            field_type_errors = [
                f"Field '{field}' should be of type {required_fields[field].__name__}"
                for field in required_fields
                if not isinstance(claim.get(field), required_fields[field])
            ]

            if field_type_errors:
                errors.append({"index": idx, "error": ", ".join(field_type_errors)})
                continue

            # Add the claim to the valid claims list if it passed all checks
            valid_claims.append(claim)

        # If there are errors, return them
        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST, safe=False)

        if not valid_claims:
            return JsonResponse({"message": "No valid claims to process"}, status=status.HTTP_400_BAD_REQUEST, safe=False)

        # Extract the list of IDs from the valid claims
        incoming_ids = [claim['Id'] for claim in valid_claims]

        # Check which IDs already exist in the database
        existing_claims = Claim.objects.filter(Id__in=incoming_ids)
        existing_ids = set(existing_claims.values_list('Id', flat=True))

        # Filter out the claims that already exist
        new_claims = [claim for claim in valid_claims if claim['Id'] not in existing_ids]

        if not new_claims:
            return JsonResponse({"message": "All valid claims already exist"}, status=status.HTTP_200_OK, safe=False)

        # Serialize the new claims
        claims_serializer = ClaimSerializer(data=new_claims, many=True)

        # Validate and save the non-existing claims
        if claims_serializer.is_valid():
            claims_serializer.save()
            return JsonResponse({
                "message": "Claims added successfully",
                "added_claims": new_claims,
                "existing_ids": list(existing_ids),
            }, status=status.HTTP_201_CREATED, safe=False)

        # Return validation errors from the serializer
        return JsonResponse(claims_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)