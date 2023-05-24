from django.contrib.auth.models import User

from rest_framework import serializers


class AdminUserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='admin-user-detail')
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = ('url', User.USERNAME_FIELD, 'email', 'date_joined')
