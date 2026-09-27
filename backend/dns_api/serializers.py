from rest_framework import serializers

from backend.app.models import RecordCreate, RecordUpdate


class RecordSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    type = serializers.ChoiceField(choices=["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SRV", "CAA"])
    name = serializers.CharField(min_length=1, max_length=255)
    data = serializers.CharField(min_length=1, max_length=4096)
    ttl = serializers.IntegerField(min_value=60, max_value=2147483647, default=600)
    priority = serializers.IntegerField(min_value=0, max_value=65535, required=False, allow_null=True)
    weight = serializers.IntegerField(min_value=0, max_value=65535, required=False, allow_null=True)
    port = serializers.IntegerField(min_value=0, max_value=65535, required=False, allow_null=True)
    service = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    protocol = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    flags = serializers.IntegerField(min_value=0, max_value=255, required=False, allow_null=True)
    tag = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status = serializers.CharField(read_only=True)

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("must not be blank")
        return value

    def validate_data(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("must not be blank")
        return value

    def to_record_create(self) -> RecordCreate:
        return RecordCreate(**self.validated_data)

    def to_record_update(self) -> RecordUpdate:
        return RecordUpdate(**self.validated_data)
