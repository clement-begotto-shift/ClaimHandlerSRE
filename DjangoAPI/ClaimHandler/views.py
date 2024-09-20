from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import ClaimSerializer
from .models import Claim


class ClaimHandlerView(APIView):

    @swagger_auto_schema(
            method = 'get',
            manual_parameters=[
                openapi.Parameter('Id', openapi.IN_QUERY,description="Id of the claim", type=openapi.TYPE_INTEGER,required=False)
            ],
            responses={200: "Claim found.", "404": "Claim not found."}
    )
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

    @swagger_auto_schema(
        method='post',
        request_body=ClaimSerializer(many=True),
        responses={201: 'Created', 200: 'Already exist', 400: 'Bad request.'}
    )
    @api_view(['POST'])
    def post(request):
        try:
            # Parse the incoming request data
            claim_data = JSONParser().parse(request)
        except Exception as e:
            return JsonResponse({"error": "Malformed JSON body", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST, safe=False)

        # Check if the incoming data is a list
        if not isinstance(claim_data, list):
            return JsonResponse({"error": "Expected a list of claims"}, status=status.HTTP_400_BAD_REQUEST, safe=False)

        incoming_ids = []
        missing_ids = []
        for idx, incoming_claim in enumerate(claim_data):
            claim_id = incoming_claim.get('Id', None)
            if claim_id == None or not str(claim_id).isdigit():
                missing_ids.append(idx)
            else:
                incoming_ids.append(claim_id)
        
        if missing_ids:
            return JsonResponse({
                "error": "Some claims have malformed or no id",
                "index_with_missing_ids":list(missing_ids)
                }, status=status.HTTP_400_BAD_REQUEST, safe=False)

        # Check which IDs already exist in the database
        existing_claims = Claim.objects.filter(Id__in=incoming_ids)
        existing_ids = set(existing_claims.values_list('Id', flat=True))

        # Filter out the claims that already exist
        new_claims = [claim for claim in claim_data if claim['Id'] not in existing_ids]

        if len(new_claims) == 0:
            return JsonResponse({
                "message": "All valid claims already exist",
                "existing_ids": list(existing_ids),
                # "errors": errors
                }, status=status.HTTP_200_OK, safe=False)

        # Serialize the new claims
        claims_serializer = ClaimSerializer(data=new_claims, many=True)

        # Validate and save the non-existing claims
        if claims_serializer.is_valid():
            claims_serializer.save()
            return JsonResponse({
                "message": f"{len(new_claims)} Claims added successfully",
                "added_claims": new_claims,
                "existing_ids": list(existing_ids),
                # "errors": errors
            }, status=status.HTTP_201_CREATED, safe=False)

        # Return validation errors from the serializer
        return JsonResponse(claims_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)