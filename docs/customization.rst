.. _customization:

Workflow & schema customization
===============================

You are not satisfied with your generated schema? Follow these steps in order to get your
schema closer to your API.

.. note:: The warnings emitted by ``./manage.py spectacular --file schema.yaml --validate``
  are intended as an indicator to where `drf-spectacular` discovered issues.
  Sane fallbacks are used wherever possible and some warnings might not even be relevant to you.
  The remaining issues can be solved with the following steps.


Step 1: ``queryset`` and ``serializer_class``
---------------------------------------------
Introspection heavily relies on those two attributes. ``get_serializer_class()``
and ``get_serializer()`` are also used if available. You can also set those
on ``APIView``. Even though this is not supported by DRF, `drf-spectacular` will pick
them up and use them.


Step 2: :py:class:`@extend_schema <drf_spectacular.utils.extend_schema>`
------------------------------------------------------------------------
Decorate your view functions with the :py:func:`@extend_schema <drf_spectacular.utils.extend_schema>` decorator.
There is a multitude of override options, but you only need to override what was not properly
discovered in the introspection.

.. code-block:: python

    class PersonView(viewsets.GenericViewSet):
        @extend_schema(
            request=YourRequestSerializer,
            responses=YourResponseSerializer,
            # more customizations
        )
        def retrieve(self, request, *args, **kwargs)
            # your code

Step 3: :py:class:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>` and type hints
---------------------------------------------------------------------------------------------------
Custom ``SerializerField``s might not get picked up properly. You can inform `drf-spectacular`
on what is to be expected with the :py:func:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>`
decorator. It takes either basic types or a ``Serializer`` as argument. In case of basic types
(e.g. str int etc.) a type hint is already sufficient.

.. code-block:: python

    @extend_schema_field(OpenApiTypes.BYTE)  # also takes basic python types
    class CustomField(serializers.Field):
        def to_representation(self, value):
            return urlsafe_base64_encode(b'\xf0\xf1\xf2')


You can apply it also to the method of a `SerializerMethodField`.

.. code-block:: python

    class ErrorDetailSerializer(serializers.Serializer):
        field_custom = serializers.SerializerMethodField()

        @extend_schema_field(OpenApiTypes.DATETIME)
        def get_field_custom(self, object):
            return '2020-03-06 20:54:00.104248'

Step 4: Extensions
------------------
The core purpose of extensions is to make the above customization mechanisms also available for library code.
Usually, you cannot easily decorate or modify ``View``, ``Serializer`` or ``Field`` from libraries.
Extensions provide a way to hook into the introspection without actually touching the library.

All extensions work on the same principle. You provide a ``target_class`` (import path
string or actual class) and then state what `drf-spectcular` should use instead of what
it would normally discover.


Replace views with :py:class:`OpenApiViewExtension <drf_spectacular.extensions.OpenApiViewExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Many libraries use ``@api_view`` or ``APIView`` instead of `ViewSet` or `GenericAPIView`.
In those cases, introspection has very little to work with. The purpose of this extension
is to augment or switch out the encountered view (only for schema generation). Simply extending
the discovered class (``class Fixed(self.target_class)``) with a ``queryset`` or
``serializer_class`` attribute will often solve most issues.

.. code-block:: python

    class Fix4(OpenApiViewExtension):
        target_class = 'oscarapi.views.checkout.UserAddressDetail'

        def view_replacement(self):
            from oscar.apps.address.models import UserAddress

            class Fixed(self.target_class):
                queryset = UserAddress.objects.none()
            return Fixed

Specify authentication with :py:class:`OpenApiAuthenticationExtension <drf_spectacular.extensions.OpenApiAuthenticationExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Authentication classes that do not have 3rd party support will emit warnings and be ignored.
Luckily authentication extensions are very easy to implement. Have a look at the
`default authentication method extensions <https://github.com/tfranzel/drf-spectacular/blob/master/drf_spectacular/authentication.py>`_.

Declare field output with :py:class:`OpenApiSerializerFieldExtension <drf_spectacular.extensions.OpenApiSerializerFieldExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is mainly targeted to custom `SerializerField`'s that are within library code. This extension
is functionally equivalent to :py:func:`@extend_schema_field <drf_spectacular.utils.extend_schema_field>`

.. code-block:: python

    class CategoryFieldFix(OpenApiSerializerFieldExtension):
        target_class = 'oscarapi.serializers.fields.CategoryField'

        def map_serializer_field(self, auto_schema, direction):
            # equivalent to return {'type': 'string'}
            return build_basic_type(OpenApiTypes.STR)


Declare serializer magic with :py:class:`OpenApiSerializerExtension <drf_spectacular.extensions.OpenApiSerializerExtension>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This is one of the more involved extension mechanisms. `drf-spectacular` uses those to implement
`polymorphic serializers <https://github.com/tfranzel/drf-spectacular/blob/master/drf_spectacular/serializers.py>`_.
The usage of this extension is rarely necessary because most custom ``Serializer`` classes stay very
close to the default behaviour.


Step 5: Postprocessing hooks
----------------------------

The generated schema is still not to your liking? You are no easy customer, but there is one
more thing you can do. Postprocessing hooks run at the very end of schema generation. This is how
the choice ``Enum`` are consolidated into component objects. You can register additional hooks with the
``POSTPROCESSING_HOOKS`` setting.

.. code-block:: python

    def custom_hook(result, generator, request, public):
        # your modifications to the schema in parameter result
        return result


Congratulations
---------------

You should now have no more warnings and a spectacular schema that satisfies all your requirements.
If that is not the case, feel free to open an `issue <https://github.com/tfranzel/drf-spectacular/issues>`_
and make a suggestion for improvement.
