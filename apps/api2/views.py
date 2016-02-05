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
        case = 0

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 

        if data is None:
            data = ''

        filter_keys_in_data = set(['id','name','url','sku']) & set(data)
        if len(filter_keys_in_data) < 1:
            case = 1
        elif len(filter_keys_in_data) > 1:
            case = 2
        else:
            # Setting up filters to query for product
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
                case = 3
            else:
                try:
                    product = Product.objects.get(filters)
                    case = 4
                except Product.DoesNotExist:
                    case = 5
                except Product.MultipleObjectsReturned:
                    case = 6
        
        if case == 1:
            return_dict['status'] = "Expecting one of id, name, or url for search, got none."
        if case == 2:
            return_dict['status'] = "Expecting one of id, name, or url for search, but got multiple: {}.".format("".join(list(filter_keys_in_data)))
        if case == 3:
            return_dict['status'] = "Expecting a number as input, but got non-number."
        if case == 4:
            return_dict['status'] = "Product with " + key[0] + ": " + str(data[key[1]]) + " has been found."
        if case == 5:
            return_dict['status'] = "Product with " + key[0] + ": " + str(data[key[1]]) + " could not be found."
        if case == 6:
            return_dict['status'] = "Multiple products with " + key[0] + ": " + str(data[key[1]]) + " have been found."

        return Response(return_dict)

    @list_route(methods=['post'])
    def scrape(self, request):
        return_dict = {"status": ""}
        case = 1

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 

        if data is None:
            data = ''

        if len(data) < 2:
            case = 1

        if not 'url' in data:
            case = 2
        elif not 'page_id' in data:
            case = 3  
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

            case = 4

        if case == 1:
            return_dict['status'] = "Expecting 2 data input but got 0 or 1."
        if case == 2:
            return_dict['status'] = "No URL found."
        if case == 3:
            return_dict['status'] = "No Page ID found."
        if case == 4:
            return_dict['status'] = "Scraped!"

        return Response(return_dict)


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

    @list_route(methods=['post'])
    def search(self, request):
        product = None
        return_dict = {"status": None}
        data = None

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 

        if data is None:
            data = ''

        filter_keys_in_data = set(['id','name','url']) & set(data) # intersection
        if len(filter_keys_in_data) < 1:
            case = 1
        elif len(filter_keys_in_data) > 1:
            case = 2
        else:
            # Setting up filters to query for content
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
                case = 3
            else:
                try:
                    content = Content.objects.get(filters)
                except Content.DoesNotExist:
                    case = 4
                except Content.MultipleObjectsReturned:
                    case = 5
                else:
                    case = 6
                    
        if case == 1:
            return_dict['status'] = "Expecting one of id, name, or url for search, got none."
        if case == 2:
            return_dict['status'] = "Expecting one of id, name, or url for search, but got multiple: {}.".format("".join(list(filter_keys_in_data)))
        if case == 3:
            return_dict['status'] = "Expecting a number as input, but got non-number."
        if case == 4:
            return_dict['status'] = "Content with " + key[0] + ": " + str(data[key[1]]) + " could not be found."
        if case == 5:
            return_dict['status'] = "Multiple contents with " + key[0] + ": " + str(data[key[1]]) + " have been found."
        if case == 6:
            return_dict['status'] = "Content with " + key[0] + ": " + str(data[key[1]]) + " has been found."

        return Response(return_dict)

    @list_route(methods=['post'])
    def upload_cloudinary(self, request):
        data = None

        return_dict = {"status": ""}

        if request.POST:
            data = request.POST
        elif request.body:
            data = ast.literal_eval(request.body) 

        if data is None:
            data = ''

        if len(data) < 2:
            case = 1

        if not 'url' in data:
            case = 2
        elif not 'page_id' in data:
            case = 3
        else:
            #Uploading happens here
            case = 4

        if case == 1:
            return_dict['status'] = "Expecting 2 data input but got 0 or 1."
        if case == 2:
            return_dict['status'] = "No URL found."
        if case == 3:
            return_dict['status'] = "No Page ID found."
        if case == 4:
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
        add_type = data.get('type')

        if not selection:
            case = 1
        elif not num:
            case = 2
        elif not add_type:
            case = 3
        else:
            # Priority checking (Check to see if priority exists & priority is a number)
            if not priority:
                priority = 0
            else:
                try:
                    priority = int(priority)
                except ValueError:
                    case = 4
                    error = True
                else:
                    error = False
            
            # Category checking (Check to see if category exists)
            if not category:
                category = None
            else:
                try:
                    category = Category.objects.get(name=category)
                except Category.DoesNotExist:
                    case = 5
                    error = True
                else:
                    error = False

            if not error:
                # Setting up filters to query for product
                selection = selection.upper()
                filters = Q(store=page.store)
                try: 
                    if selection == 'URL':
                        filters = filters & Q(url=num)
                    elif selection == 'SKU':
                        if add_type == 'product':
                            num = int(num)
                            filters = filters & Q(sku=num)
                        else:
                            raise AttributeError
                    elif selection == 'ID':
                        num = int(num)
                        filters = filters & Q(id=num)
                    else:
                        raise TypeError
                except ValueError:
                    case = 6
                except TypeError:
                    case = 7
                except AttributeError:
                    case = 8
                else:
                    if add_type == 'product':
                        try:
                            product = Product.objects.get(filters)
                        except Product.DoesNotExist:
                            case = 9
                        except Product.MultipleObjectsReturned:
                            case = 10
                        else:
                            if page.feed.tiles.filter(products=product, template="product"):
                                case = 11
                            else:
                                page.feed.add(product,priority=priority,category=category)
                                # Additional check to make sure adding succeeded
                                if page.feed.tiles.filter(products=product, template="product"):
                                    case = 12
                                else:
                                    case = 13
                    elif add_type == 'content':
                        try:
                            content = Content.objects.get(filters)
                        except Content.DoesNotExist:
                            case = 14
                        except Content.MultipleObjectsReturned:
                            case = 15
                        else:
                            #Content adding
                            if page.feed.tiles.filter(content=content):
                                case = 16
                            else:
                                page.feed.add(content,category=category) 
                                # Additional check to make sure adding succeeded
                                if page.feed.tiles.filter(content=content):
                                    case = 17
                                else:
                                    case = 18
                    else:
                        case = 19

        if case == 1:
            status = "Missing 'selection' field from input."
        if case == 2:
            status = "Missing 'num' field from input."
        if case == 3:
            status = "Missing 'type' field from input."
        if case == 4:
            status = "Error: Priority '{}' is not a number.".format(priority)
        if case == 5:
            status = "Error: Category '{0}' not found.".format(category)
        if case == 6:
            status = "Expecting a number as input, but got non-number."
        if case == 7:
            status = "Expecting URL/SKU/ID as input, but got none."
        if case == 8:
            status = "Adding content using SKU is not allowed."
        
        if case == 9:
            status = "Product with " + selection + ": " + str(num) + ", Store: " + page.store.name + " has not been found. Add failed."
        if case == 10:
            status = "Multiple products with " + selection + ": " + str(num) + ", Store: " + page.store.name + " have been found. Add failed."
        if case == 11:
            status = "Product with " + selection + ": " + str(num) + ", Name: " + product.name + ", Store: " + page.store.name + " is already added. Add failed."
        if case == 12:
            status = "Product with " + selection + ": " + str(num) + ", Name: " + product.name + " has been added."
        if case == 13:
            status = "Adding of product with " + selection + ": " + str(num) + ", Name: " + product.name + " has failed for an unknown error."
        
        if case == 14:
            status = "Content with " + selection + ": " + str(num) + ", Store: " + page.store.name + " has not been found. Add failed."
        if case == 15:
            status = "Multiple contents with " + selection + ": " + str(num) + ", Store: " + page.store.name + " have been found. Add failed."
        if case == 16:
            status = "Content with " + selection + ": " + str(num) + ", Store: " + page.store.name + " is already added. Add failed."
        if case == 17:
            status = "Content with " + selection + ": " + str(num) + " has been added."
        if case == 18:
            status = "Adding of content with " + selection + ": " + str(num) + " has failed for an unknown error."
        if case == 19:
            status = "Error: Type '{}' is not a valid type (content/product only).".format(add_type)

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
        remove_type = data.get('type')

        if not selection:
            case = 1
        elif not num:
            case = 2
        else:
            # Setting up filters to query for product
            selection = selection.upper()
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
                case = 3
            except TypeError:
                case = 4
            else:
                if remove_type == 'product':
                    try: 
                        product = Product.objects.get(filters)
                    except Product.DoesNotExist:
                        case = 5
                    except Product.MultipleObjectsReturned:
                        case = 6
                    else:
                        if not page.feed.tiles.filter(products=product, template="product"):
                            case = 7
                        else:
                            page.feed.remove(product)
                            # Additional check to make sure removing succeeded
                            if not page.feed.tiles.filter(products=product, template="product"):
                                case = 8
                            else:
                                case = 9
                elif remove_type == 'content':
                    try:
                        content = Content.objects.get(filters)
                    except Content.DoesNotExist:
                        case = 10
                    except Content.MultipleObjectsReturned:
                        case = 11
                    else:
                        #Content removing
                        if not page.feed.tiles.filter(content=content):
                            case = 12
                        else:
                            page.feed.remove(content)
                            # Additional check to make sure removing succeeded
                            if not page.feed.tiles.filter(content=content):
                                case = 13
                            else:
                                case = 14
                else:
                    case = 15

        if case == 1:
            status = "Missing 'selection' field from input."
        if case == 2:
            status = "Missing 'num' field from input."
        if case == 3:
            status = "Expecting a number as input, but got non-number."
        if case == 4:
            status = "Expecting URL/SKU/ID as input, but got none."
        
        if case == 5:
            status = "Product with " + selection + ": " + str(num) + ", Store: " \
                        + page.store.name + " has not been found. Remove failed."
        if case == 6:
            status = "Multiple products with " + selection + ": " + str(num) + ", Store: " \
                        + page.store.name + " have been found. Remove failed."
        if case == 7:
            status = "Product with " + selection + ": " + str(num) + ", Name: " + product.name \
                        + ", Store: " + page.store.name + " has not been found. Remove failed."
        if case == 8:
            status = "Product with " + selection + ": " + str(num) + ", Name: " + product.name \
                        + " has been removed."
        if case == 9:
            status = "Product with " + selection + ": " + str(num) + ", Name: " + product.name \
                        + " could not be removed for an unknown reason."
        
        if case == 10:
            status = "Content with " + selection + ": " + str(num) + ", Store: " \
                        + page.store.name + " has not been found. Remove failed."
        if case == 11:
            status = "Multiple contents with " + selection + ": " + str(num) + ", Store: " \
                        + page.store.name + " have been found. Remove failed."
        if case == 12:
            status = "Content with " + selection + ": " + str(num) + ", Store: " + page.store.name + " is already removed. Removal failed."
        if case == 13:
            status = "Content with " + selection + ": " + str(num) + " has been removed."
        if case == 14:
            status = "Removal of content with " + selection + ": " + str(num) + " has failed for an unknown error."
        if case == 15:
            status = "Error: Type '{}' is not a valid type (content/product only).".format(remove_type)

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
