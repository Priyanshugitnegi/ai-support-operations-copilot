
from rest_framework import serializers
from .models import Ticket,TicketAnalysis


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class TicketAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAnalysis
        fields = "__all__"
        read_only_fields = ("id", "created_at")
