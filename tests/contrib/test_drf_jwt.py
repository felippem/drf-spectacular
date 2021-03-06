from django.urls import path
from rest_framework import serializers, viewsets, mixins, routers

from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.views import obtain_jwt_token

from drf_spectacular.generators import SchemaGenerator
from tests import assert_schema


class XSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()


class XViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XSerializer
    authentication_classes = [JSONWebTokenAuthentication]
    required_scopes = ['x:read', 'x:write']


def test_drf_jwt(no_warnings):
    router = routers.SimpleRouter()
    router.register('x', XViewset, basename="x")

    urlpatterns = [
        *router.urls,
        path('api-token-auth/', obtain_jwt_token, name='get_token'),
    ]

    generator = SchemaGenerator(patterns=urlpatterns)
    schema = generator.get_schema(request=None, public=True)

    assert_schema(schema, 'tests/contrib/test_drf_jwt.yml')
