import ast, json
from multiprocessing import Process
from urlparse import urlparse

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import connection 
from django.db.models import Q
from django.http import Http404, QueryDict
from django.shortcuts import get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError

from rest_framework import permissions, renderers, status, viewsets
from rest_framework.decorators import api_view, detail_route, list_route
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_bulk import generics, BulkListSerializer

from apps.assets.models import Category, Content, Feed, Gif, Image, Page, Product, ProductImage, Store, Tile, Video
from apps.dashboard.models import Dashboard, UserProfile
from apps.imageservice.tasks import process_image
from apps.intentrank.algorithms import ir_magic
from apps.scrapy.controllers import PageMaintainer
from .serializers import CategorySerializer, ContentSerializer, FeedSerializer, GifSerializer, ImageSerializer, \
    PageSerializer, ProductSerializer, ProductImageSerializer, StoreSerializer, TileSerializer, TileSerializerBulk, \
    VideoSerializer
from .generics import ListCreateDestroyBulkUpdateAPIView


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @list_route(methods=['get'])
    def bulk(self, request):
        """
        Returns a list of products based on given product IDs

        inputs:
            list of product ids

        returns:
            list of serialized products
        """
        return_dict = []

        if request.data == {}:
            products = request.GET
        elif request.GET == {}:
            products = request.data
        else:
            products = []

        if type(products) is QueryDict:
            products = dict(products.iterlists())

        products = products.get('data', products.get('data[]', None))
        
        if type(products) is unicode:
            products = ast.literal_eval(products)

        try:
            for x in range(0, len(products)):
                if products[x] is not int:
                    products[x] = int(products[x])
        except ValueError:
            return_dict = 'Error. One of the IDs provided is not a number.'
        except TypeError:
            if type(products) is int:
                product = get_object_or_404(Product, pk=products)
                return_dict = (ProductSerializer(product).data)
        else:
            for p in products:
                product = get_object_or_404(Product, pk=p)
                return_dict.append(ProductSerializer(product).data)

        return Response(return_dict)


    @list_route(methods=['post'])
    def search(self, request):
        """
        Search for product

        inputs:
            id/url/name/sku: any of the 4 as an input to search from

        returns:
            status: status message containing result of search task
            ids: list of id/ids of product/products found
            product: 
        """
        return_dict = {'status': None, 'ids': [], 'products': []}
        
        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        # Compare the data keys with approved keys list and put found keys in a new array
        filter_keys_in_data = set(['id', 'name', 'url', 'sku']) & set(data)
        if len(filter_keys_in_data) < 1:
            return_dict['status'] = u"Expecting one of id, name, sku or url for search, got none."
            status_code = 400
        elif len(filter_keys_in_data) > 1:
            return_dict['status'] = (u"Expecting one of id, name, sku or url for search, but got "
                                    "multiple: {}.").format(" ".join(list(filter_keys_in_data)))
            status_code  = 400
        else:
            # Setting up filters to query for product
            id_filter = data.get('id', None)
            name_filter = data.get('name', None)
            sku_filter = data.get('sku', None)
            url_filter = data.get('url', None)
            filters = None
            try:
                if id_filter:
                    id_filter = int(id_filter)
                    key = ('ID', 'id')
                    filters = Q(id=id_filter)

                if name_filter:
                    key = ('name', 'name')
                    filters = Q(name=name_filter)

                if sku_filter:
                    sku_filter = int(sku_filter)
                    key = ('SKU', 'sku')
                    filters = Q(sku=sku_filter)

                if url_filter:
                    validator = URLValidator()
                    try:
                        validator(url_filter)
                    except ValidationError:
                        raise Exception("Bad URL input detected.")
                    key = ('URL', 'url')
                    filters = Q(url=url_filter)
            except (ValueError, TypeError):
                return_dict['status'] = u"Expecting a number as input, but got non-number."
                status_code = 400
            except Exception as e:
                return_dict['status'] = str(e)
                status_code = 400
            else:
                try:
                    product = Product.objects.get(filters)
                except Product.DoesNotExist:
                    return_dict['status'] = u"Product with {0}: {1} could not be found.".format(key[0], str(data[key[1]]))
                    status_code = 404
                except Product.MultipleObjectsReturned:
                    products = Product.objects.filter(filters)
                    status_parts = [u"Multiple products have been found. IDs:"]
                    for p in products:
                        status_parts.append(str(p['id']))
                        return_dict['ids'].append(p['id'])
                        return_dict['products'].append(ProductSerializer(p).data)
                    return_dict['status'] = " ".join(status_parts)
                    status_code = 200
                else:
                    return_dict['status'] = u"Product found: ID {0}.".format(str(product.id))
                    return_dict['ids'].append(product.id)
                    return_dict['products'].append(ProductSerializer(product).data)
                    status_code = 200

        return Response(return_dict, status=status_code)

    @list_route(methods=['post'])
    def scrape(self, request):
        """
        Scrape for product from URL provided

        inputs:
            url: url from which the product scrape is performed
            page_id: page id from which the product scrape is performed

        returns:
            status: status message containing result of scrape
            id: id of resultant product
            product: resultant product
        """

        return_dict = {'status': "", 'id': None, 'product': []}

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        if not 'url' in data:
            return_dict['status'] = u"No URL found."
            status_code  = 400
        elif not 'page_id' in data:
            return_dict['status'] = u"No Page ID found."
            status_code  = 400
        else:
            options = {
                'skip_tiles': False,
                'refresh_images': True
            }

            url = unicode(data['url'], "utf-8")

            try:
                page = Page.objects.get(id=data['page_id'])
            except Page.DoesNotExist:
                return_dict['status'] = u"Scraping has failed. Page with ID: {} not found.".format(data['page_id'])
                status_code = 404
            else:
                def process(request, page, url, options):
                    PageMaintainer(page).add(source_urls=[url], options=options)

                # Close the connection so that once the scrape process completes
                # There won't be multiple processes trying to use the same socket
                # Which causes "DatabaseError: SSL error: decryption failed or bad record mac"
                connection.close()
                
                p = Process(target=process, args=[request, page, url, options])
                p.start()
                p.join()

                try:
                    product = Product.objects.get(url=url)
                except Product.DoesNotExist:
                    return_dict['status'] = u"Scraping has failed. Product Not Found."
                    status_code = 404
                else:
                    return_dict['status'] = u"Scraping has succeeded. Product ID: {}".format(product.id)
                    return_dict['id'] = product.id
                    return_dict['product'] = ProductSerializer(product).data
                    status_code = 200

        return Response(return_dict, status=status_code)


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

    @list_route(methods=['get'])
    def bulk(self, request):
        """
        Returns a list of contents based on given content IDs

        inputs:
            list of content ids

        returns:
            list of serialized contents
        """
        return_dict = []

        if request.data == {}:
            contents = request.GET
        elif request.GET == {}:
            contents = request.data
        else:
            contents = []

        if type(contents) is QueryDict:
            contents = dict(contents.iterlists())

        contents = contents.get('data', contents.get('data[]', None))
        
        if type(contents) is unicode:
            contents = ast.literal_eval(contents)

        try:
            for x in range(0, len(contents)):
                if contents[x] is not int:
                    contents[x] = int(contents[x])
        except ValueError:
            return_dict = 'Error. One of the IDs provided is not a number.'
        except TypeError:
            if type(contents) is int:
                content = get_object_or_404(Content, pk=contents)
                return_dict = (ContentSerializer(content).data)
        else:
            for c in contents:
                content = get_object_or_404(Content, pk=c)
                return_dict.append(ContentSerializer(content).data)

        return Response(return_dict)

    @list_route(methods=['post'])
    def search(self, request):
        """
        Search for content

        inputs:
            id/url/name: any of the 3 as an input to search from

        returns:
            status: status message containing result of search task
            ids: list of id/ids of content/contents found
            content: resultant added content
        """

        return_dict = {'status': None, 'ids': [], 'contents': []}

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        # Compare the data keys with approved keys list and put found keys in a new array
        filter_keys_in_data = set(['id', 'name', 'url']) & set(data) # intersection
        if len(filter_keys_in_data) < 1:
            return_dict['status'] = u"Expecting one of id, name, or url for search, got none."
            status_code = 400
        elif len(filter_keys_in_data) > 1:
            return_dict['status'] = (u"Expecting one of id, name, or url for search, but got "
                                    "multiple: {}.").format(" ".join(list(filter_keys_in_data)))
            status_code = 400
        else:
            # Setting up filters to query for content
            id_filter = data.get('id', None)
            name_filter = data.get('name', None)
            url_filter = data.get('url', None)
            filters = None
            try:
                if id_filter:
                    id_filter = int(id_filter)
                    key = ('ID', 'id')
                    filters = Q(id=id_filter)

                if name_filter:
                    key = ('name', 'name')
                    filters = Q(name=name_filter)

                if url_filter:
                    validator = URLValidator()
                    try:
                        validator(url_filter)
                    except ValidationError:
                        raise Exception("Bad URL input detected.")
                    key = ('URL', 'url')
                    parsed_url = urlparse(url_filter)
                    if 'secondfunnel' in parsed_url.netloc or 'cloudinary' in parsed_url.netloc:
                        filters = Q(url=url_filter)
                    else:
                        filters = Q(source_url=url_filter)
            except (ValueError, TypeError):
                return_dict['status'] = u"Expecting a number as input, but got non-number."
                status_code = 400
            except Exception as e:
                return_dict['status'] = str(e)
                status_code = 400
            else:
                try:
                    content = Content.objects.get(filters)
                except Content.DoesNotExist:
                    return_dict['status'] = u"Content with {0}: {1} could not be found.".format(key[0], str(data[key[1]]))
                    status_code = 404
                except Content.MultipleObjectsReturned:
                    contents = Content.objects.filter(filters)
                    status_parts = [u"Multiple contents have been found. IDs:"]
                    for c in contents:
                        status_parts.append(str(c['id']))
                        return_dict['ids'].append(c['id'])
                        return_dict['contents'].append(ContentSerializer(c).data)
                    return_dict['status'] = " ".join(status_parts)
                    status_code = 200
                else:
                    return_dict['status'] = u"Content with {0}: {1} has been found.".format(key[0], str(data[key[1]]))
                    return_dict['ids'].append(content.id)       
                    return_dict['contents'].append(ContentSerializer(content).data)
                    status_code = 200

        return Response(return_dict, status=status_code)

    @list_route(methods=['post'])
    def scrape(self, request):
        """
        Upload content to cloudinary and create an image object along with it

        inputs:
            url: url from which image is uploaded

        returns:
            status: status message containing result of upload and image ID if successful
            url: if upload successful, url of uploaded image on cloudinary
            image: if upload successful, image object created
            error: if upload unsuccessful, error messages returned by cloudinary
        """
        return_dict = {'status': "", 'image': []}
        status_code = 400

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        page = get_object_or_404(Page, pk=data['page_id'])
        store = get_object_or_404(Store, pk=page.store_id)

        if not 'url' in data:
            return_dict['status'] = "No URL found."
        else:
            try:
                img_obj = process_image(data['url'])
            except Exception as e:
                return_dict['status'] = u"Upload failed. Error: {}".format(str(e))
                return_dict['error'] = str(e)
            else:
                if 'error' in img_obj:
                    return_dict['status'] = u"Upload failed. Error: {}".format(img_obj['error']['http_code'])
                    return_dict['error'] = img_obj['error']
                else:
                    kwargs = {
                        "store_id": page.store_id,
                        "file_type": img_obj['format'],
                        "attributes": {"sizes": img_obj['sizes']},
                        "dominant_color": img_obj['dominant_color'],
                        "source": "upload",
                        "source_url": data['url'],
                        "url": img_obj['sizes']['master']['url'],
                        "width": img_obj['sizes']['master']['width'],
                        "height": img_obj['sizes']['master']['height'],
                    }
                    image = Image(**kwargs)
                    image.save()

                    return_dict['status'] = u"Uploaded. Image ID: {}".format(image.id)
                    return_dict['id'] = image.id
                    return_dict['image'] = ImageSerializer(image).data
                    status_code = 200


        return Response(return_dict, status=status_code)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer


class GifViewSet(viewsets.ModelViewSet):
    queryset = Gif.objects.all()
    serializer_class = GifSerializer


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    @list_route(methods=['get'])
    def bulk(self, request):
        """
        Returns a list of product images based on given product image IDs

        inputs:
            list of product image ids

        returns:
            list of serialized product images
        """
        return_dict = []

        if request.data == {}:
            productImagess = request.GET
        elif request.GET == {}:
            productImagess = request.data
        else:
            productImagess = []

        if type(productImagess) is QueryDict:
            productImagess = dict(productImagess.iterlists())

        productImagess = productImagess.get('data', productImagess.get('data[]', None))
        
        if type(productImagess) is unicode:
            productImagess = ast.literal_eval(productImagess)

        try:
            for x in range(0, len(productImagess)):
                if productImagess[x] is not int:
                    productImagess[x] = int(productImagess[x])
        except ValueError:
            return_dict = 'Error. One of the IDs provided is not a number.'
        except TypeError:
            if type(productImagess) is int:
                productImage = get_object_or_404(ProductImage, pk=productImagess)
                return_dict = (ProductImageSerializer(productImage).data)
        else:
            for pi in productImagess:
                productImage = get_object_or_404(ProductImage, pk=pi)
                return_dict.append(ProductImageSerializer(productImage).data)

        return Response(return_dict)


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def retrieve(self, request, pk):
        """
        Overrides the default GET response for single tiles to also display categories
        """
        try:
            page = Page.objects.get(pk=pk)
        except Page.DoesNotExist:
            status = {u'detail': u'Not found.'}
            status_code = 404
        else:
            p_categories = []
            if page.feed is not None:
                for c in page.feed.categories.all():
                    p_categories.append({'id': c.id, 'name': c.name })
            status = PageSerializer(page).data
            status['categories'] = p_categories
            status_code = 200
            
        return Response(status, status=status_code)

    def add_product(self, filters, product_id, page, category=None, priority=None, force_create_tile=False):  
        """
        Adds product to page, with optional category and/or priority

        inputs:
            filters: filters corresponding to product query requirements
            product_id: product ID
            page: page on which to add product
            category: (optional) category name
            priority: (optional) priority number to assign to new tile

        returns:
            status: status message containing result of add task
            tile: newly created tile
            success: True if add succeeded, False if product not found
        """

        tile = None

        try:
            product = Product.objects.get(filters)
        except Product.DoesNotExist:
            status = (u"Product with ID: {0}, Store: {1} has not been found. Add failed."
                      "").format(str(product_id), page.store.name)
            success = False
        except Product.MultipleObjectsReturned:
            status = (u"Multiple products with ID: {0}, Store: {1} have been found. Add "
                      "failed.").format(str(product_id), page.store.name)
            raise AttributeError(status)
        else:
            if page.feed.tiles.filter(products=product, template="product") and not force_create_tile:
                status = (u"Product with ID: {0}, Name: {1}, Store: {2} is already added. "
                          "Add failed.").format(str(product_id), product.name, page.store.name)
                raise AttributeError(status)
            else:                
                (tile, result) = page.feed.add(product, priority=priority, category=category, force_create_tile=force_create_tile) 
                if result:
                    status = u"Product with ID: {0}, Name: {1} has been added.".format(str(product_id), product.name)
                    success = True
                else:
                    status = (u"Adding of product with ID: {0}, Name: {1} has failed due to "
                              "an unknown error.").format(str(product_id), product.name)
                    raise AttributeError(status)

        return (status, tile, success)

    def remove_product(self, filters, product_id, page, category=None):
        """
        Remove product from page

        inputs:
            filters: filters corresponding to product query requirements
            product_id: product ID
            page: page on which to add product
            category: (optional) <Category> object

        returns:
            status: status message containing result of remove task
            success: True if remove succeeded, False if product not found
        """
        try: 
            product = Product.objects.get(filters)
        except Product.DoesNotExist:
            status = (u"Product with ID: {0}, Store: {1} has not been found. "
                      "Remove failed.").format(str(product_id), page.store.name)
            success = False
        except Product.MultipleObjectsReturned:
            status = (u"Multiple products with ID: {0}, Store: {1} have been found. "
                      "Remove failed.").format(str(product_id), page.store.name)
            raise AttributeError(status)
        else:
            query = Q(products=product, template="product")
            if category:
                query &= Q(categories=category)
            if not page.feed.tiles.filter(query):
                status = (u"Product with ID: {0}, Name: {1}, Store: {2} has not been "
                          "found. Remove failed.").format(str(product_id), product.name, page.store.name)
                raise AttributeError(status)
            else:
                page.feed.remove(product, category=category)
                status = u"Product with ID: {0}, Name: {1} has been removed.".format(str(product_id), product.name)
                success = True

        return (status, success)

    def add_content(self, filters, content_id, page, category=None, priority=None, force_create_tile=False):
        """
        Adds content to page, with optional category

        inputs:
            filters: filters corresponding to content query requirements
            content_id: content ID
            page: page on which to add content
            category: (optional) category name

        returns:
            status: status message containing result of add task
            tile: newly created tile
            success: True if add succeeded, False if content not found
        """

        tile = None

        try:
            content = Content.objects.get(filters)
        except Content.DoesNotExist:
            status = (u"Content with ID: {0}, Store: {1} has not been found. Add "
                      "failed.").format(str(content_id), page.store.name)
            success = False
        except Content.MultipleObjectsReturned:
            status = (u"Multiple contents with ID: {0}, Store: {1} have been found. "
                      "Add failed.").format(str(content_id), page.store.name)
            raise AttributeError(status)
        else:
            # Content adding
            if page.feed.tiles.filter(content=content) and not force_create_tile:
                status = (u"Content with ID: {0}, Store: {1} is already added. Add "
                          "failed.").format(str(content_id), page.store.name)
                raise AttributeError(status)
            else:
                (tile, result) = page.feed.add(content, priority=priority, category=category, force_create_tile=force_create_tile) 
                if result:
                    status = u"Content with ID: {0} has been added.".format(str(content_id))
                    success = True
                else:
                    status = (u"Adding of content with ID: has failed due to an unknown "
                              "error.").format(str(content_id)) 
                    raise AttributeError(status)
          
        return (status, tile, success)

    def remove_content(self, filters, content_id, page, category=None):
        """
        Remove content from page

        inputs:
            filters: filters corresponding to content query requirements
            content_id: content ID
            page: page on which to add product
            category: (optional) <Category> object

        returns:
            status: status message containing result of remove task
            success: True if remove succeeded, False if content not found
        """
                
        try:
            content = Content.objects.get(filters)
        except Content.DoesNotExist:
            status = (u"Content with ID: {0}, Store: {1} has not been found. Remove "
                      "failed.").format(str(content_id), page.store.name)
            success = False
        except Content.MultipleObjectsReturned:
            status = (u"Multiple contents with ID: {0}, Store: {1} have been found. "
                      "Remove failed.").format(str(content_id), page.store.name)
            raise AttributeError(status)
        else:
            # Content removing
            query = Q(content=content)
            if category:
                query &= Q(categories=category)
            if not page.feed.tiles.filter(query):
                status = (u"Content with ID: {0}, Store: {1} has not been found. "
                          "Remove failed.").format(str(content_id), page.store.name)
                raise AttributeError(status)
            else:
                page.feed.remove(content, category=category)
                status = "Content with ID: {0} has been removed.".format(str(content_id))
                success = True
        
        return (status, success)

    @detail_route(methods=['get'])
    def products(self, request, pk):
        """
        List all products available for this page, up to a limit set by return_dict

        inputs:
            id: page ID

        returns:
            list of dictionaries containing product details for page
        """
        # Set the maximum number of results to return
        return_limit = 100

        profile = UserProfile.objects.get(user=self.request.user)
        page = get_object_or_404(Page, pk=pk)
        store = get_object_or_404(Store, pk=page.store_id)
        return_dict = {}

        # Handle both products query ie /products?id=XXXX and /products data="{'id':XXXX}"
        data = request.data.get('data', {})
        if type(data) is not dict:
            data = ast.literal_eval(request.data.get('data', {}))

        if data == {}:
            # Test if the format's /products?id=XXXX or not
            data = request.GET

        # Setting up filters to query for product
        id_filter = data.get('id', data.get('ID', None))
        sku_filter = data.get('sku', data.get('SKU', None))
        url_filter = data.get('url', data.get('URL', None))
        name_filter = data.get('name', data.get('Name', None))

        filters = Q(store=store)
        try:
            if id_filter:
                id_filter = int(id_filter)
                filters = filters & Q(id__icontains=id_filter)
            elif sku_filter:
                sku_filter = int(sku_filter)
                filters = filters & Q(sku__icontains=sku_filter)
            elif name_filter:
                filters = filters & Q(name__icontains=name_filter)
            elif url_filter:
                filters = filters & Q(url__icontains=url_filter)
        except ValueError:
            return_dict['status'] = "Expecting a number as input, but got non-number."
            status_code = 400
        except Exception as e:
            return_dict['status'] = str(e)
            status_code = 400
        else:
            products = Product.objects.filter(filters).order_by('-id')

            serialized_products = [ {'id': p.id, 'name': p.name, } for p in products[:return_limit]]

            return_dict = serialized_products
            status_code = 200
        
        return Response(return_dict, status=status_code)

    @detail_route(methods=['get'])
    def contents(self, request, pk):
        """
        List all contents available for this page, up to a limit set by return_dict

        inputs:
            id: page ID

        returns:
            list of dictionaries containing content details for page
        """
        # Set the maximum number of results to return
        return_limit = 100

        profile = UserProfile.objects.get(user=self.request.user)
        page = get_object_or_404(Page, pk=pk)
        store = get_object_or_404(Store, pk=page.store_id)
        return_dict = {}

        # Handle both contents query ie /contents?id=XXXX and /contents data="{'id':XXXX}"
        data = request.data.get('data', {})
        if type(data) is not dict:
            data = ast.literal_eval(request.data.get('data', {}))

        if data == {}:
            # Test if the format's /contents?id=XXXX or not
            data = request.GET

        # Setting up filters to query for product
        id_filter = data.get('id', data.get('ID', None))
        url_filter = data.get('url', data.get('URL', None))

        filters = Q(store=store)
        try:
            if id_filter:
                id_filter = int(id_filter)
                filters = filters & Q(id__icontains=id_filter)
            elif url_filter:
                filters = filters & Q(url__icontains=url_filter)
        except ValueError:
            return_dict['status'] = "Expecting a number as input, but got non-number."
            status_code = 400
        except Exception as e:
            return_dict['status'] = str(e)
            status_code = 400
        else:
            contents = Content.objects.filter(filters).order_by('-id')

            serialized_contents = [ {'id': c.id, 'name': c.name, } for c in contents[:return_limit]]

            return_dict = serialized_contents
            status_code = 200
        
        return Response(return_dict, status=status_code)

    @detail_route(methods=['post'])
    def add(self, request, pk):
        """
        Adds product or content to page, with optional category and/or priority

        inputs:
            id: product or content ID
            category: (optional) category name
            priority: (optional) priority number to assign to new tile
            force_create_tile: (optional) force create tiles or not
            type: what type the id is: 'product' or 'content'

        returns:
            status: status message
            id: ID of newly created tile
        """

        tile = None
        
        try:
            page = Page.objects.get(pk=pk)
        except Page.DoesNotExist:
            status = u"Page with ID: {} not found.".format(pk)
            status_code = 404
        else:
            success = None
            status_code = 400
            
            try:
                data = request.POST or ast.literal_eval(request.body)
            except SyntaxError:
                data = {}

            obj_id = data.get('id', None)
            category = data.get('category', None)
            priority = data.get('priority', 0)
            add_type = data.get('type', None)

            force_create_tile = bool(data.get('force_create_tile') in ["True", "true"])
            if not obj_id:
                status = "Missing 'id' field from input."
            elif not add_type:
                status = "Missing 'type' field from input."
            else:
                try:
                    # Priority checking (Check to see if priority exists & priority is a number)
                    try:
                        priority = int(priority)
                    except ValueError:
                        raise RuntimeError(u"Priority '{}' is not a number.".format(priority))
                    # Check if category exists
                    if category:
                        try:
                            category = Category.objects.get(name=category, store=page.store)
                        except Category.DoesNotExist:
                            raise RuntimeError(u"Category '{0}' not found for store '{1}'.".format(category, page.store.name))
                except RuntimeError as e:
                    status = e.args[0].encode('ascii', 'ignore')
                else:
                    # Setting up filters to query for product
                    filters = Q(store=page.store)
                    try: 
                        obj_id = int(obj_id)
                        filters = filters & Q(id=obj_id)
                    except ValueError:
                        status = "Expecting a number as input, but got non-number."
                    else:
                        # Use add_product if the type's product, else use add_content
                        try:
                            if add_type == 'product':
                                (status, tile, success) = self.add_product(filters, obj_id, page, category, priority, force_create_tile)
                            elif add_type == 'content':
                                (status, tile, success) = self.add_content(filters, obj_id, page, category, priority, force_create_tile)
                            else:
                                raise AttributeError(u"Type '{}' is not a valid type (content/product only).".format(add_type))
                        except AttributeError as e:
                            status = e.args[0].encode('ascii', 'ignore')
                        else:
                            status_code = 200 if success else 404
   
        response = {
            "status": status
        }

        if tile:
            response['id'] = tile.id
            response['tile'] = TileDetail.get_serialized_tile(TileDetail(), tile)
                 
        return Response(response, status=status_code)

    @detail_route(methods=['post'])
    def remove(self, request, pk):
        """
        Remove product or content from page

        inputs:
            id: product or content ID
            category: (optional) category name
            type: what type the id is: 'product' or 'content'

        returns:
            status: status message
        """

        try:
            page = Page.objects.get(pk=pk)
        except Page.DoesNotExist:
            status = "Page with ID: {} not found.".format(pk)
            status_code = 404
        else:
            success = None
            status_code = 400

            try:
                data = request.POST or ast.literal_eval(request.body)
            except SyntaxError:
                data = {}

            obj_id = data.get('id', None)
            category = data.get('category', None)
            remove_type = data.get('type', None)

            if not obj_id:
                status = "Missing 'id' field from input."
            elif not remove_type:
                status = "Missing 'type' field from input."
            else:
                # Setting up filters to query for product
                filters = Q(store=page.store)
                try: 
                    obj_id = int(obj_id)
                    filters = filters & Q(id=obj_id)
                except ValueError:
                    status = "Expecting a number as input, but got non-number."
                else: 
                    try:
                        # Check if category exists
                        if category:
                            try:
                                category = Category.objects.get(name=category, store=page.store)
                            except Category.DoesNotExist:
                                raise RuntimeError(u"Category '{0}' not found for store '{1}'.".format(category, page.store.name))
                    except RuntimeError as e:
                        status = e.args[0].encode('ascii', 'ignore')
                    else:               
                        # Use remove_product if the type's product, else use remove_content
                        try:
                            if remove_type == 'product':
                                (status, success) = self.remove_product(filters, obj_id, page, category)
                            elif remove_type == 'content':
                                (status, success) = self.remove_content(filters, obj_id, page, category)
                            else:
                                raise AttributeError(u"Type '{}' is not a valid type (content/product only).".format(remove_type))
                        except AttributeError as e:
                            status = e.args[0].encode('ascii', 'ignore')
                        else:
                            status_code = 200 if success else 404

        return Response({
            "status": status,
        }, status=status_code)


# Individual tile details
class TileDetail(APIView):
    serializer_class = TileSerializerBulk
    queryset = Tile.objects.all()

    def get_serialized_tile(self, tile):
        """
        Returns the serialized tile complete with image URL and name

        inputs:
            tile: <Tile> object to be serialized

        returns:
            serialized_tile: <dict> containing tile details
        """
        serialized_tile = TileSerializer(tile).data

        if tile['template'] == 'product':
            product =  tile['products'].first()
            if product is not None:
                if product.default_image is not None:
                    serialized_tile['defaultImage'] = product.default_image.url
                else:
                    serialized_tile['defaultImage'] = ''
                serialized_tile['name'] = product.name
            else:
                serialized_tile['defaultImage'] = ''
                serialized_tile['name'] = 'No name'
        else:
            content = tile['content'].first()
            if content is not None:
                serialized_tile['defaultImage'] = content.url
                if content.name is None:
                    serialized_tile['name'] = 'No name'
                else:
                    serialized_tile['name'] = content.name
            else:
                serialized_tile['defaultImage'] = ''
                serialized_tile['name'] = 'No name'

        return serialized_tile

    def tile_tagger(self, tile, products, contents):
        try:
            for p in products:
                p = get_object_or_404(Product, pk=p)
                tile.products.add(p)
            for c in contents:
                c = get_object_or_404(Content, pk=c)
                tile.content.add(c)
        except Exception as e:
            status = str(e)
            status_code = 400
        else:
            status = "Tile tagging was successful."
            status_code = 200
        return (status, status_code)

    def post(self, request, pk, method):
        profile = UserProfile.objects.get(user=self.request.user)
        tile = get_object_or_404(Tile, pk=pk)

        return_dict = {}

        if method == 'tag':
            data = request.data.get('data', {})
            if type(data) is not dict:
                data = ast.literal_eval(request.data.get('data', {}))

            products = data.get('products', [])
            contents = data.get('contents', [])
            try:
                page_id = data['pageID']
            except KeyError:
                (status, status_code) = ("Missing pageID parameter.", 400)
            else:
                page = get_object_or_404(Page, pk=page_id)
                store = get_object_or_404(Store, pk=page.store_id)
                if tile.feed != page.feed:
                    (status, status_code) = ("Tile is not part of this page.", 400)
                else:
                    # Now need to check if the products/contents listed are part of tile store
                    for p in products:
                        p = get_object_or_404(Product, pk=p)
                        if p.store_id != store.id:
                            return_dict['detail'] = "Product with ID: " + str(p.id) + " is not part of the " + store.name + " store."
                            status = 400
                            return Response(return_dict, status=status)
                    for c in contents:
                        c = get_object_or_404(Content, pk=c)
                        if c.store_id != store.id:
                            return_dict['detail'] = "Content with ID: " + str(c.id) + " is not part of the " + store.name + " store."
                            status = 400
                            return Response(return_dict, status=status)
                    (status, status_code) = self.tile_tagger(tile, products, contents)
        else:
            (status, status_code) = ("Method not allowed.", 403)

        return_dict = {'detail': status}

        return Response(return_dict, status=status_code)

    def get(self, request, pk, format=None):
        """
        Returns the serialized tile

        inputs: 

        returns:
            serialized tile
        """        
        profile = UserProfile.objects.get(user=self.request.user)
        tile = get_object_or_404(Tile, pk=pk)
        dashboards = profile.dashboards.all()

        tile_in_user_dashboards = bool(Dashboard.objects.filter(userprofiles=profile, page__feed__tiles=tile).count())

        if tile_in_user_dashboards:
            status = self.get_serialized_tile(tile)
            status_code = 200
        else:
            status = "Not allowed."
            status_code = 400

        return Response(status, status=status_code)

    def patch(self, request, pk, format=None):
        """
        Patches the tile with pk given to new attribute

        inputs: 
            one of the tile attributes (ex priority)

        returns:
            serialized tile
        """        
        profile = UserProfile.objects.get(user=self.request.user)
        tile = get_object_or_404(Tile, pk=pk)

        status = {"detail": "Not allowed"}
        status_code = 400

        if 'attributes' in request.data:
            attributes = request.data.get('attributes')
            if type(attributes) is unicode:
                request.data['attributes'] = ast.literal_eval(request.data['attributes'])

        tile_in_user_dashboards = bool(Dashboard.objects.filter(userprofiles=profile, page__feed__tiles=tile).count())

        if tile_in_user_dashboards:
            serializer = TileSerializer(tile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                status = serializer.data
                status_code = 200
            else:
                status = serializer.errors

        return Response(status, status=status_code)

    def delete(self, request, pk):
        """
        Delete the tile with pk given

        inputs:

        returns:
        """
        profile = UserProfile.objects.get(user=self.request.user)
        tile = get_object_or_404(Tile, pk=pk)

        tile_in_user_dashboards = bool(Dashboard.objects.filter(userprofiles=profile, page__feed__tiles=tile).count())

        if tile_in_user_dashboards:
            tile.delete()
            status = "Successfully deleted tile with ID: " + pk + "."
            status_code = 200
        else:
            status = "Not allowed"
            status_code = 400

        return Response(status, status=status_code)


#Bulk tile details
class TileViewSetBulk(ListCreateDestroyBulkUpdateAPIView):
    serializer_class = TileSerializerBulk
    queryset = Tile.objects.all()
    list_serializer_class = BulkListSerializer

    def get(self, request):
        """
        Returns the serialized tile

        inputs: 

        returns:
            serialized tile or status message of errors
        """
        request_get = request.GET

        status = "Missing page parameter."
        status_code = 400

        if not request_get == {}:
            if 'page' in request_get:
                profile = UserProfile.objects.get(user=self.request.user)
                dashboards = profile.dashboards.all()
                
                tiles = None

                try:
                    request_id = int(request_get['page'])
                except ValueError:
                    pass
                else:
                    try:
                        page = Page.objects.get(pk=request_id)
                    except Page.DoesNotExist:
                        pass
                    else:
                        page_in_user_dashboard = bool(Dashboard.objects.filter(userprofiles=profile, page=page).count())
                        if page_in_user_dashboard:
                            tiles = ir_magic(page.feed.tiles, num_results=page.feed.tiles.count())

                if tiles is not None:
                    serialized_tiles = []
                    for t in tiles:
                        serialized_data = TileDetail.get_serialized_tile(TileDetail(), t)
                        t_categories = []
                        for c in t.categories.all():
                            t_categories.append({'id': c.id, 'name': c.name })
                        serialized_data['categories'] = t_categories

                        serialized_tiles.append(serialized_data)
                    status = serialized_tiles
                    status_code = 200
                else:
                    status = "No tiles found."
                    status_code = 404
            else:
                status = "Not allowed."

        return Response(status, status_code)


class FeedViewSet(viewsets.ModelViewSet):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


@api_view(('GET',))
def api_root(request, format=None):
    """
    Displays the Root API webpage

    inputs:
        No inputs

    returns:
        A dict containing all the models you can view through API
    """

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
