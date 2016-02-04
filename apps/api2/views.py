import ast
from multiprocessing import Process

from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import generics
from rest_framework.decorators import api_view, detail_route, list_route
from rest_framework.response import Response
from rest_framework.reverse import reverse

from apps.assets.models import Store, Product, Content, Image, Gif, ProductImage, Video, Page, Tile, Feed, Category
from apps.scrapy.controllers import PageMaintainer
from serializers import StoreSerializer, ProductSerializer, ContentSerializer, ImageSerializer, GifSerializer, \
    ProductImageSerializer, VideoSerializer, PageSerializer, TileSerializer, FeedSerializer, CategorySerializer


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @list_route(methods=['post'])
    def search(self, request):
        data = None
        return_dict = {"status": None}

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 
        else:
            return_dict['status'] = "Too few inputs."

        if data is None:
            data = ''

        if len(data) < 1:
            return_dict['status'] = "Expecting data input but got none."
        elif len(data) > 1:
            return_dict['status'] = "Expecting 1 set of data but got multiple."
        else:
            key = None
            filters = None
            id_filter = data.get('id', None)
            name_filter = data.get('name', None)
            sku_filter = data.get('sku', None)
            url_filter = data.get('url', None)
            try:
                if id_filter:
                    id_filter = int(id_filter)
                    key = ('ID','id')
                    filters = Q(id=id_filter)

                if name_filter:
                    key = ('name','name')
                    filters = Q(name=name_filter)

                if sku_filter:
                    sku_filter = int(sku_filter)
                    key = ('SKU','sku')
                    filters = Q(sku=sku_filter)

                if url_filter:
                    key = ('URL', 'url')
                    filters = Q(url=url_filter)
            except (ValueError, TypeError):
                return_dict['status'] = "Expecting a number as input, but got non-number."
            else:
                try:
                    product = Product.objects.get(filters)
                    return_dict['status'] = "Product with " + key[0] + ": " + str(data[key[1]]) + " has been found."
                except Product.DoesNotExist:
                    return_dict['status'] = "Product with " + key[0] + ": " + str(data[key[1]]) + " could not be found."
                except Product.MultipleObjectsReturned:
                    return_dict['status'] = "Multiple products with " + key[0] + ": " + str(data[key[1]]) + " have been found."
        
        return Response(return_dict)

    @list_route(methods=['post'])
    def scrape(self, request):
        return_dict = {"status": ""}

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 
        else:
            return_dict['status'] = "Too few inputs."

        if data is None:
            data = ''

        if len(data) < 2:
            return_dict['status'] = "Expecting 2 data input but got 0 or 1."

        if not 'url' in data:
            return_dict['status'] = "No URL found."
        elif not 'page_id' in data:
            return_dict['status'] = "No Page ID found."
        else:
            categories = None
            priorities = None

            options = {
                'skip_tiles': False,
                'refresh_images': True
            }

            url = [data['url']]
            page = None
            if 'page_id' in data:
                page = Page.objects.get(pk=data['page_id'])

            def process(request, page, url, options, categories, priorities):
                maintainer = PageMaintainer(page)
                maintainer.add(source_urls=url, categories=categories, options=options)

            p = Process(target=process, args=[request, page, url, options, categories, priorities])
            p.start()
            p.join()

            return_dict['status'] = "Scraped!"

        return Response(return_dict)


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

    @list_route(methods=['post'])
    def search(self, request):
        product = None
        return_dict = {"status": None}

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 
        else:
            return_dict['status'] = "Too few inputs."

        if data is None:
            data = ''

        if len(data) < 1:
            return_dict['status'] = "Expecting data input but got none."
        elif len(data) > 1:
            return_dict['status'] = "Expecting 1 set of data but got multiple."
        else:
            key = None
            filters = None
            id_filter = data.get('id', None)
            name_filter = data.get('name', None)
            url_filter = data.get('url', None)
            try:
                if id_filter:
                    id_filter = int(id_filter)
                    key = ('ID','id')
                    filters = Q(id=id_filter)

                if name_filter:
                    key = ('name','name')
                    filters = Q(name=name_filter)

                if url_filter:
                    key = ('URL', 'url')
                    filters = Q(url=url_filter)
            except (ValueError, TypeError):
                return_dict['status'] = "Expecting a number as input, but got non-number."
            else:
                try:
                    content = Content.objects.get(filters)
                    return_dict['status'] = "Content with " + key[0] + ": " + str(data[key[1]]) + " has been found."
                except Content.DoesNotExist:
                    return_dict['status'] = "Content with " + key[0] + ": " + str(data[key[1]]) + " could not be found."
                except Content.MultipleObjectsReturned:
                    return_dict['status'] = "Multiple contents with " + key[0] + ": " + str(data[key[1]]) + " have been found."
        
        return Response(return_dict)

    @list_route(methods=['post'])
    def upload_cloudinary(self, request):
        data = None

        return_dict = {"status": ""}

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 
        else:
            return_dict['status'] = "Too few inputs."

        if data is None:
            data = ''

        if len(data) < 2:
            return_dict['status'] = "Expecting 2 data input but got 0 or 1."

        if not 'url' in data:
            return_dict['status'] = "No URL found."
        elif not 'page_id' in data:
            return_dict['status'] = "No Page ID found."
        else:
            #Uploading happens here
            return_dict['status'] = "Uploaded!"

        return Response(return_dict)


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

    @detail_route(methods=['post'])
    def add(self, request, pk):
        add_type = None
        error = False
        data = None
        page = Page.objects.get(pk=pk)

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body)

        if data is None:
            data = {}

        selection = data.get('selection')
        num = data.get('num')
        category = data.get('category')
        priority = data.get('priority')

        if not selection:
            status = ["Missing 'selection' field from input."]
        elif not num:
            status = ["Missing 'num' field from input."]
        else:
            if not priority:
                priority = 0
            else:
                try:
                    priority = int(priority)
                except ValueError:
                    status = ["Error: Priority '{}' is not a number.".format(priority)]
                    error = True
                else:
                    error = False

            if not category:
                category = None
            else:
                try:
                    category = Category.objects.get(name=category)
                except Category.DoesNotExist:
                    status = ["Error: Category '{0}' not found.".format(category)]
                    error = True
                else:
                    error = False

            if not error:
                selection = selection.upper()
                status = ["Product with " + selection + ": " + str(num)]
                filters = Q(store=page.store)
                try: 
                    if selection == 'URL':
                        filters = filters & Q(url=num)
                    elif selection == 'SKU':
                        num = int(num)
                        filters = filters & Q(sku=num)
                    elif selection == 'ID':
                        num = int(num)
                        filters = filters & Q(id=num)
                    else:
                        raise TypeError
                except ValueError:
                    status = ["Expecting a number as input, but got non-number."]
                except TypeError:
                    status = ["Expecting URL/SKU/ID as input, but got none."]
                else:
                    try:
                        product = Product.objects.get(filters)
                    except Product.DoesNotExist:
                        status.append(", Store: " + page.store.name + " has not been found. Add failed.")
                    except Product.MultipleObjectsReturned:
                        status = ["Multiple products with " + selection + ": " + str(num) + ", Store: " \
                            + page.store.name + " have been found. Remove failed."]
                    else:
                        status.append(", Name: " + product.name)

                        if page.feed.tiles.filter(products=product, template="product"):
                            status.append(", Store: " + page.store.name + " is already added. Add failed.")
                        else:
                            page.feed.add(product,priority=priority,category=category)
                            status.append(" has been added.")

        status = "".join(status)

        return Response({
            "action": "Add",
            "slug": pk,
            "store_name": page.store.name,
            "selection": selection,
            "num": num,
            "status": status,
            })

    @detail_route(methods=['post'])
    def remove(self, request, pk):
        status = None
        data = None
        page = Page.objects.get(pk=pk)

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body)

        if data is None:
            data = {}

        selection = data.get('selection')
        num = data.get('num')
        if not selection:
            status = ["Missing 'selection' field from input."]
        elif not num:
            status = ["Missing 'num' field from input."]
        else:
            selection = selection.upper()
            status = ["Product with " + selection + ": " + str(num)]
            filters = Q(store=page.store)
            try: 
                if selection == 'URL':
                    filters = filters & Q(url=num)
                elif selection == 'SKU':
                    num = int(num)
                    filters = filters & Q(sku=num)
                elif selection == 'ID':
                    num = int(num)
                    filters = filters & Q(id=num)
                else:
                    raise TypeError
            except ValueError:
                status = ["Expecting a number as input, but got non-number."]
            except TypeError:
                status = ["Expecting URL/SKU/ID as input, but got none."]
            else:
                try: 
                    product = Product.objects.get(filters)
                except Product.DoesNotExist:
                    status.append(", Store: " + page.store.name + " has not been found. Remove failed.")
                except Product.MultipleObjectsReturned:
                    status = ["Multiple products with " + selection + ": " + str(num) + ", Store: " \
                        + page.store.name + " have been found. Remove failed."]
                else:
                    status.append(", Name: " + product.name)
                    if not page.feed.tiles.filter(products=product, template="product"):
                        status.append(", Store: " + page.store.name + " has not been found. Remove failed.")
                    else:
                        page.feed.remove(product)
                        status.append(" has been removed.")

        status = "".join(status)

        return Response({
            "action": "Remove",
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
