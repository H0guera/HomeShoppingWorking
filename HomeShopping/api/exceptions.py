from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import status

from rest_framework.views import exception_handler
from rest_framework.response import Response


def django_error_handler(exc, context):
    """Handle django core's errors."""
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    if response is None and isinstance(exc, ValidationError):
        return Response(status=400, data=exc.messages)
    if isinstance(exc, IntegrityError) and not response:
        response = Response(
            {
                'message': 'It seems there is a conflict between the data you are trying to save and your current '
                           'data. Please review your entries and try again.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    return response

