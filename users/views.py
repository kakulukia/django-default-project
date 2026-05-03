from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.data.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_staff:
            return queryset
        return queryset.filter(pk=user.pk)

    @action(detail=False, methods=["get"])
    def me(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
