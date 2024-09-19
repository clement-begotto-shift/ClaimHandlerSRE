from rest_framework import serializers
from ClaimHandler.models import Claim

class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ('Id', 'ClaimName', 'Verified')