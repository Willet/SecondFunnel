from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import renderers, viewsets, generics

from apps.assets.models import Store, Product, Content, Image, Gif, ProductImage, Video, Page, Tile
from serializers import StoreSerializer, ProductSerializer, ContentSerializer, ImageSerializer, GifSerializer, \
                        ProductImageSerializer, VideoSerializer, PageSerializer, TileSerializer

class StoreList(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ContentList(generics.ListAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

class ImageList(generics.ListAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class GifList(generics.ListAPIView):
    queryset = Gif.objects.all()
    serializer_class = GifSerializer

class ProductImageList(generics.ListAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

class VideoList(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

class PageList(generics.ListAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

class TileList(generics.ListAPIView):
    queryset = Tile.objects.all()
    serializer_class = TileSerializer

@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'store': reverse('store-list', request=request, format=format),
        'product': reverse('product-list', request=request, format=format),
        'content': reverse('content-list', request=request, format=format),
        'image': reverse('image-list', request=request, format=format),
        'gif': reverse('gif-list', request=request, format=format),
        'productimage': reverse('productimage-list', request=request, format=format),
        'video': reverse('video-list', request=request, format=format),
        'page': reverse('page-list', request=request, format=format),
        'tile': reverse('tile-list', request=request, format=format)
    })
