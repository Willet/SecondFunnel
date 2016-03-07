import ast

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from rest_framework_bulk import mixins as bulk_mixins

class PatchBulkUpdateModelMixin(bulk_mixins.BulkUpdateModelMixin):
    # Overriding the built-in bulk_update to allow for user to send PATCH requests
    # through a client like httpie. 
    def bulk_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        if isinstance(request.data, list):
            data = request.data[0]
        else:
            data = request.data

        if 'data' in data:
            data = ast.literal_eval(data['data'])

        # restrict the update to the filtered queryset
        serializer = self.get_serializer(
            self.filter_queryset(self.get_queryset()),
            data=data,
            many=True,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
        

class ListCreateDestroyBulkUpdateAPIView(mixins.ListModelMixin,
                                      mixins.CreateModelMixin,
                                      mixins.DestroyModelMixin,
                                      PatchBulkUpdateModelMixin,
                                      GenericAPIView
                                      ):
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.bulk_update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.bulk_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
