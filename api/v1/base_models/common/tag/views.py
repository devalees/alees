from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from taggit.models import Tag
from .serializers import TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for the taggit Tag model.
    This viewset doesn't inherit from OrganizationScopedViewSetMixin as Tags are global
    and not bound to a specific organization.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search tags by name.
        """
        query = request.query_params.get('q', '')
        tags = Tag.objects.filter(name__icontains=query)
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data) 