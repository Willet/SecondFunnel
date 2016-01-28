import ast

from django.contrib.auth.models import User
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import generics
from rest_framework.decorators import api_view, detail_route
from rest_framework.response import Response
from rest_framework.reverse import reverse

from apps.assets.models import Store, Product, Content, Image, Gif, ProductImage, Video, Page, Tile, Feed, Category
from serializers import StoreSerializer, ProductSerializer, ContentSerializer, ImageSerializer, GifSerializer, \
    ProductImageSerializer, VideoSerializer, PageSerializer, TileSerializer, FeedSerializer, CategorySerializer


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def post(self, request, *args, **kwargs):
        method = kwargs.get('pk')
        data = ''
        product = ''
        found = 0
        key = []

        if request.POST == {}:
            data = ast.literal_eval(request.body)
        else:
            data = request.POST
        if len(data) < 1:
            return Response({"status": "too few inputs"})

        if method == 'search':
            if 'id' in data:
                key = ['ID','id']
                try:
                    data['id'] = int(data['id'])
                except ValueError:
                    return Response({"status": "Please enter a number"})
                product = Product.objects.filter(pk = data['id'])

            if 'name' in data:
                key = ['name','name']
                product = Product.objects.filter(name = data['name'])

            if 'sku' in data:
                key = ['SKU','sku']
                try:
                    data['sku'] = int(data['sku'])
                except ValueError:
                    return Response({"status": "Please enter a number"})
                product = Product.objects.filter(sku = data['sku'])

            if 'url' in data:
                key = ['URL', 'url']
                product = Product.objects.filter(url = data['url'])

            if product:
                return Response({"status": "Product with " + key[0] + ": " + str(data[key[1]]) + " has been found."})
            else:
                return Response({"status": "Product with " + key[0] + ": " + str(data[key[1]]) + " could not be found."})

        return Response({"detail": "Method 'POST' not allowed."}, 405)

    @detail_route(methods=['post'])
    def search(self, request, *args, **kwargs):
        return Response("search func")
        

class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


class GifViewSet(viewsets.ModelViewSet):
    queryset = Gif.objects.all()
    serializer_class = GifSerializer


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def post(self, request, pk, *args, **kwargs):
        return Response("post")

    @detail_route(methods=['post'])
    def add(self, request, pk, *args, **kwargs):
        action = "Add"

        if request.POST == {}:
            data = ast.literal_eval(request.body)
        else:
            data = request.POST

        if len(data) < 2:
            return Response({"status": "Too few inputs"})
        elif len(data) > 2:
            return Response({"status": "Too many inputs"})

        selection = data['selection'].upper()
        num = data['num']

        page = Page.objects.get(pk=pk)

        status = ["Product with " + selection + ": " + num]

        product = ''
        if selection == 'URL':
            product = Product.objects.filter(store=page.store, url=num)
        elif selection == 'SKU':
            product = Product.objects.filter(store=page.store, sku=num)
        elif selection == 'ID':
            product = Product.objects.filter(store=page.store, id=num)

        if not product:
            status.append(", Store: " + page.store.name + " has not been found. " + action + " failed.")
        else: 
            status.append(", Name: " + product.first().name)
            if page.feed.tiles.filter(products=product, template="product"):
                status.append(", Store: " + page.store.name + " is already added. " + action + " failed.")
            else:
                page.feed.add(product.first())
                status.append(" has been added")

        status = "".join(status)

        return Response({
            "action": action,
            "slug": pk,
            "store_name": page.store.name,
            "selection": selection,
            "num": num,
            "status": status,
            })

    @detail_route(methods=['post'])
    def remove(self, request, pk, *args, **kwargs):
        action = "Remove"

        if request.POST == {}:
            data = ast.literal_eval(request.body)
        else:
            data = request.POST

        if len(data) < 2:
            return Response({"status": "Too few inputs"})
        elif len(data) > 2:
            return Response({"status": "Too many inputs"})

        selection = data['selection'].upper()
        num = data['num']

        page = Page.objects.get(pk=pk)

        status = ["Product with " + selection + ": " + num]

        product = ''
        if selection == 'URL':
            product = Product.objects.filter(store=page.store, url=num)
        elif selection == 'SKU':
            product = Product.objects.filter(store=page.store, sku=num)
        elif selection == 'ID':
            product = Product.objects.filter(store=page.store, id=num)

        if not product:
            status.append(", Store: " + page.store.name + " has not been found. " + action + " failed.")
        else: 
            status.append(", Name: " + product.first().name)
            if not page.feed.tiles.filter(products=product, template="product"):
                status.append(", Store: " + page.store.name + " has not been found. " + action + " failed.")
            else:
                page.feed.remove(product.first())
                status.append(" has been removed")

        status = "".join(status)

        return Response({
            "action": action,
            "slug": pk,
            "store_name": page.store.name,
            "selection": selection,
            "num": num,
            "status": status,
            })
        
class TileViewSet(viewsets.ModelViewSet):
    queryset = Tile.objects.all()
    serializer_class = TileSerializer


class FeedViewSet(viewsets.ModelViewSet):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer


class CategoryViewSet(viewsets.ModelViewSet):
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
