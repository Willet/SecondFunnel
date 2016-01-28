from serializers import StoreSerializer, ProductSerializer, ContentSerializer, ImageSerializer, GifSerializer, \
    ProductImageSerializer, VideoSerializer, PageSerializer, TileSerializer, FeedSerializer, CategorySerializer

from django.contrib.auth.models import User

from rest_framework import renderers
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from apps.assets.models import Store, Product, Content, Image, Gif, ProductImage, Video, Page, Tile, Feed, Category

import ast

class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

class StoreList(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def post(self, request, *args, **kwargs):
        return {"Found"}

class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

class ContentList(generics.ListAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class ImageList(generics.ListAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

class GifViewSet(viewsets.ModelViewSet):
    queryset = Gif.objects.all()
    serializer_class = GifSerializer

class GifList(generics.ListAPIView):
    queryset = Gif.objects.all()
    serializer_class = GifSerializer

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

class ProductImageList(generics.ListAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

class VideoList(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

class PageList(generics.ListAPIView):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def post(self, request, *args, **kwargs):
        print "request.body"
        print request.body
        print type(request.body)
        print "request.POST"
        print request.POST
        print type(request.POST)

        action = kwargs.get('method').lower()
        slug = kwargs.get('id')

        if request.POST == {}:
            data = ast.literal_eval(request.body)
        else:
            data = request.POST

        if len(data) < 2:
            return Response("too few inputs")
        elif len(data) > 2:
            return Response("too many inputs")

        selection = data['selection'].upper()
        num = data['num']

        page = Page.objects.get(pk=slug)

        status = ["Product with " + selection + ": " + num]

        product = ''
        if selection == 'URL':
            product = Product.objects.filter(store=page.store, url=num)
        elif selection == 'SKU':
            product = Product.objects.filter(store=page.store, sku=num)
        else:
            product = Product.objects.filter(store=page.store, id=num)

        if not product:
            status.append(", Store: " + page.store.name + " has not been found. " + action + " failed.")
        else: 
            status.append(", Name: " + product.first().name)

            if action == 'add':
                if page.feed.tiles.filter(products=product, template="product"):
                    status.append(", Store: " + page.store.name + " is already added. " + action + " failed.")
                else:
                    page.feed.add(product.first())
                    status.append(" has been added")
            elif action == 'remove':
                if not page.feed.tiles.filter(products=product, template="product"):
                    status.append(", Store: " + page.store.name + " has not been found. " + action + " failed.")
                else:
                    page.feed.remove(product.first())
                    status.append(" has been removed")

        status = "".join(status)
        print {
            "action": action,
            "slug": slug,
            "store_name": page.store.name,
            "selection": selection,
            "num": num,
            "status": status,
            }

        return Response({
            "action": action,
            "slug": slug,
            "store_name": page.store.name,
            "selection": selection,
            "num": num,
            "status": status,
            })

    def add(self,id):
        return 1

    def remove(self,id):
        return 1

class TileViewSet(viewsets.ModelViewSet):
    queryset = Tile.objects.all()
    serializer_class = TileSerializer

class TileList(generics.ListAPIView):
    queryset = Tile.objects.all()
    serializer_class = TileSerializer

class FeedViewSet(viewsets.ModelViewSet):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer

class FeedList(generics.ListAPIView):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'store': reverse('store-list', request=request, format=format),
        'product': reverse('product-list', request=request, format=format),
        'content': reverse('content-list', request=request, format=format),
        'image': reverse('image-list', request=request, format=format),
        'gif': reverse('gif-list', request=request, format=format),
        'productimage': reverse('productimage-list', request=request, format=format),
        'page': reverse('page-list', request=request, format=format),
        'tile': reverse('tile-list', request=request, format=format),
        'feed': reverse('feed-list', request=request, format=format),
        'category': reverse('category-list', request=request, format=format)
    })
