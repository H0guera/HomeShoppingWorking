from django.contrib.auth.models import User
from rest_framework import generics, status, response
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.login import UserSerializer, LoginSerializer
from api.utils.session import login_and_upgrade_session


class LoginView(APIView):
    serializer_class = LoginSerializer

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            ser = UserSerializer(request.user, many=False)
            return Response(ser.data)
        raise MethodNotAllowed("GET")

    def post(self, request, *args, **kwargs):
        ser = self.serializer_class(data=request.data)
        if ser.is_valid():

            user = ser.instance

            # refuse to login logged in users, to avoid attaching sessions to
            # multiple users at the same time.
            if request.user.is_authenticated:
                return Response(
                    {"detail": "Session is in use, log out first"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
                )

            request.user = user

            login_and_upgrade_session(request._request, user)

            return Response("")

        return Response(ser.errors, status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, *args, **kwargs):
        """
        Destroy the session.
        for anonymous users that means having their basket destroyed as well,
        because there is no way to reach it otherwise.
        """
        request = request._request
        if request.user.is_anonymous:
            response.delete_cookie('open_basket')

        request.session.flush()

        return Response("")



class UserDetail(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)
