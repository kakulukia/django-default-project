from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer
from utils import IsOwnerOrSuperAdmin


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.data.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrSuperAdmin]

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
