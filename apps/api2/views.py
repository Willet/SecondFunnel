import ast
from multiprocessing import Process

from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import renderers, viewsets, permissions, generics
from rest_framework.decorators import api_view, detail_route, list_route
from rest_framework.response import Response
from rest_framework.reverse import reverse

from apps.assets.models import Store, Product, Content, Image, Gif, ProductImage, Video, Page, Tile, Feed, Category
from apps.scrapy.controllers import PageMaintainer
from .serializers import StoreSerializer, ProductSerializer, ContentSerializer, ImageSerializer, GifSerializer, \
    ProductImageSerializer, VideoSerializer, PageSerializer, TileSerializer, FeedSerializer, CategorySerializer


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @list_route(methods=['post'])
    def search(self, request):
        """
        Search for product

        inputs:
            id/url/name/sku: any of the 4 as an input to search from

        returns:
            status: status message containing result of search task
            ids: list of id/ids of product/products found
        """
        return_dict = {'status': None, 'ids': []}
        
        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = ''

        # Compare the data keys with approved keys list and put found keys in a new array
        filter_keys_in_data = set(['id','name','url','sku']) & set(data)
        if len(filter_keys_in_data) < 1:
            return_dict['status'] = "Expecting one of id, name, sku or url for search, got none."
            status_code = 400
        elif len(filter_keys_in_data) > 1:
            return_dict['status'] = ("Expecting one of id, name, sku or url for search, but got "
                                    "multiple: {}.").format(" ".join(list(filter_keys_in_data)))
            status_code  = 400
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
                return_dict['status'] = "Expecting a number as input, but got non-number."
                status_code = 400
            else:
                try:
                    product = Product.objects.get(filters)
                except Product.DoesNotExist:
                    return_dict['status'] = "Product with {0}: {1} could not be found.".format(key[0],str(data[key[1]]))
                    status_code = 404
                except Product.MultipleObjectsReturned:
                    products = Product.objects.filter(filters)
                    status_parts = ["Multiple products have been found. IDs:"]
                    for p in products:
                        status_parts.append(str(p['id']))
                        return_dict['ids'].append(p['id'])
                    return_dict['status'] = " ".join(status_parts)
                    status_code = 200
                else:
                    return_dict['status'] = "Product found: ID {0}.".format(str(product.id))
                    return_dict['ids'].append(product.id)
                    status_code = 200

        return Response(return_dict, status=status_code)

    @list_route(methods=['post'])
    def scrape(self, request):
        """
        Scrape for product from URL provided

        inputs:
            url: url from which the product scrape is performed

        returns:
            status: status message containing result of scrape
            id: id of resultant product
        """

        return_dict = {'action': 'scrape', 'status': "", 'id': None, 'product': []}

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = ''

        if not 'url' in data:
            return_dict['status'] = "No URL found."
            status_code  = 400
        elif not 'page_id' in data:
            return_dict['status'] = "No Page ID found."
            status_code  = 400
        else:
            options = {
                'skip_tiles': False,
                'refresh_images': True
            }

            url = data['url']
            page = Page.objects.get(id=data['page_id'])

            def process(request, page, url, options):
                PageMaintainer(page).add(source_urls=[url], options=options)

            p = Process(target=process, args=[page, url, options])
            p.start()
            p.join()

            product = Product.objects.get(url=url)

            return_dict['status'] = "Scraped! Product ID: {}".format(product.id)
            return_dict['id'] = product.id
            return_dict['product'].append(ProductSerializer(product).data)

            status_code = 200

        return Response(return_dict, status_code)


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer

    @list_route(methods=['post'])
    def search(self, request):
        """
        Search for content

        inputs:
            id/url/name: any of the 3 as an input to search from

        returns:
            status: status message containing result of search task
            ids: list of id/ids of content/contents found
        """

        return_dict = {'status': None, 'ids': [], 'content': []}

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = ''

        # Compare the data keys with approved keys list and put found keys in a new array
        filter_keys_in_data = set(['id','name','url']) & set(data) # intersection
        if len(filter_keys_in_data) < 1:
            return_dict['status'] = "Expecting one of id, name, or url for search, got none."
            status_code = 400
        elif len(filter_keys_in_data) > 1:
            return_dict['status'] = ("Expecting one of id, name, or url for search, but got "
                                    "multiple: {}.").format(" ".join(list(filter_keys_in_data)))
            status_code = 400
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
                return_dict['status'] = "Expecting a number as input, but got non-number."
                status_code = 400
            else:
                try:
                    content = Content.objects.get(filters)
                except Content.DoesNotExist:
                    return_dict['status'] = "Content with {0}: {1} could not be found.".format(key[0],str(data[key[1]]))
                    status_code = 404
                except Content.MultipleObjectsReturned:
                    contents = Content.objects.filter(filters)
                    status_parts = ["Multiple contents have been found. IDs:"]
                    for c in contents:
                        status_parts.append(str(c['id']))
                        return_dict['ids'].append(c['id'])
                        return_dict['content'].append(ContentSerializer(c).data)
                    return_dict['status'] = " ".join(status_parts)
                    status_code = 200
                else:
                    return_dict['status'] = "Content with {0}: {1} has been found.".format(key[0], str(data[key[1]]))
                    return_dict['ids'].append(content.id)       
                    return_dict['content'].append(ContentSerializer(content).data)
                    status_code = 200

        return Response(return_dict, status_code)

    @list_route(methods=['post'])
    def scrape(self, request):
        """
        Upload content to cloudinary

        inputs:
            url: url from which image is uploaded

        returns:
            status: status message containing result of upload
            id: id of resultant image
        """

        return_dict = {'action': 'scrape', 'status': "", 'id': None, 'image': []}

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = ''

        if len(data) < 1:
            return_dict['status'] = "Expecting 1 data input but got 0."
            status_code = 400
        elif not 'url' in data:
            return_dict['status'] = "No URL found."
            status_code = 400
        else:
            img_obj = upload_to_cloudinary(data['url'])
            return_dict['status'] = "Uploaded. Image ID: {}".format(img_obj.id)
            return_dict['id'].append(img_obj.id)
            return_dict['image'].append(ImageSerializer(img_ob).data)
            status_code = 200

        return Response(return_dict, status_code)


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

    def add_product(self, filters, product_id, page, category=None, priority=None):  
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

        tile = success = None

        try:
            product = Product.objects.get(filters)
        except Product.DoesNotExist:
            status = ("Product with ID: {0}, Store: {1} has not been found. Add failed."
                      "").format(str(product_id), page.store.name)
            success = False
        except Product.MultipleObjectsReturned:
            status = ("Multiple products with ID: {0}, Store: {1} have been found. Add "
                      "failed.").format(str(product_id), page.store.name)
        else:
            if page.feed.tiles.filter(products=product, template="product"):
                status = ("Product with ID: {0}, Name: {1}, Store: {2} is already added. "
                          "Add failed.").format(str(product_id),product.name,page.store.name)
            else:
                (tile, result) = page.feed.add(product,priority=priority,category=category)
                # Additional check to make sure adding succeeded
                if page.feed.tiles.filter(products=product, template="product"):
                    status = "Product with ID: {0}, Name: {1} has been added.".format(str(product_id), product.name)
                    success = True
                else:
                    status = ("Adding of product with ID: {0}, Name: {1} has failed due to "
                              "an unknown error.").format(str(product_id), product.name)

        if success is None:
            raise AttributeError(status)
        
        return (status, tile, success)

    def remove_product(self, filters, product_id, page):
        """
        Remove product from page

        inputs:
            filters: filters corresponding to product query requirements
            product_id: product ID
            page: page on which to add product

        returns:
            status: status message containing result of remove task
            success: True if remove succeeded, False if product not found
        """

        success = None

        try: 
            product = Product.objects.get(filters)
        except Product.DoesNotExist:
            status = ("Product with ID: {0}, Store: {1} has not been found. Remove "
                      "failed.").format(str(product_id), page.store.name)
            success = False
        except Product.MultipleObjectsReturned:
            status = ("Multiple products with ID: {0}, Store: {1} have been found. "
                      "Remove failed.").format(str(product_id), page.store.name)
        else:
            if not page.feed.tiles.filter(products=product, template="product"):
                status = ("Product with ID: {0}, Name: {1}, Store: {2} has not been "
                          "found. Remove failed.").format(str(product_id), product.name, page.store.name)
            else:
                page.feed.remove(product)
                # Additional check to make sure removing succeeded
                if not page.feed.tiles.filter(products=product, template="product"):
                    status = "Product with ID: {0}, Name: {1} has been removed.".format(str(product_id), product.name)
                    success = True
                else:
                    status = ("Product with ID: {0}, Name: {1} could not be removed due to "
                              "an unknown reason.").format(str(product_id), product.name)

        if success is None:
            raise AttributeError(status)
        
        return (status, success)

    def add_content(self, filters, content_id, page, category=None):
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

        tile = success = None
        
        try:
            content = Content.objects.get(filters)
        except Content.DoesNotExist:
            status = ("Content with ID: {0}, Store: {1} has not been found. Add "
                      "failed.").format(str(content_id), page.store.name)
            success = False
        except Content.MultipleObjectsReturned:
            status = ("Multiple contents with ID: {0}, Store: {1} have been found. "
                      "Add failed.").format(str(content_id), page.store.name)
        else:
            #Content adding
            if page.feed.tiles.filter(content=content):
                status = ("Content with ID: {0}, Store: {1} is already added. Add "
                          "failed.").format(str(content_id), page.store.name)
            else:
                (tile, status) = page.feed.add(content,category=category) 
                # Additional check to make sure adding succeeded
                if page.feed.tiles.filter(content=content):
                    status = "Content with ID: {0} has been added.".format(str(content_id))
                    success = True
                else:
                    status = ("Adding of content with ID: has failed due to an unknown "
                              "error.").format(str(content_id)) 
          
        if success is None:
            raise AttributeError(status)
          
        return (status, tile, success)

    def remove_content(self, filters, content_id, page):
        """
        Remove content from page

        inputs:
            filters: filters corresponding to content query requirements
            content_id: content ID
            page: page on which to add product

        returns:
            status: status message containing result of remove task
            success: True if remove succeeded, False if content not found
        """
        
        success = None
        
        try:
            content = Content.objects.get(filters)
        except Content.DoesNotExist:
            status = ("Content with ID: {0}, Store: {1} has not been found. Remove "
                      "failed.").format(str(content_id), page.store.name)
            success = False
        except Content.MultipleObjectsReturned:
            status = ("Multiple contents with ID: {0}, Store: {1} have been found. "
                      "Remove failed.").format(str(content_id), page.store.name)
        else:
            #Content removing
            if not page.feed.tiles.filter(content=content):
                status = ("Content with ID: {0}, Store: {1} is already removed. "
                          "Removal failed.").format(str(content_id), page.store.name)
            else:
                page.feed.remove(content)
                # Additional check to make sure removing succeeded
                if not page.feed.tiles.filter(content=content):
                    status = "Content with ID: {0} has been removed.".format(str(content_id))
                    success = True
                else:
                    status = ("Removal of content with ID: {0} has failed due to "
                              "an unknown error.").format(str(content_id))

        if success is None:
            raise AttributeError(status)
        
        return (status, success)

    @detail_route(methods=['post'])
    def add(self, request, pk):
        """
        Adds product or content to page, with optional category and/or priority

        inputs:
            id: product or content ID
            category: (optional) category name
            priority: (optional) priority number to assign to new tile
            type: what type the id is: 'product' or 'content'

        returns:
            action: action performed (Add)
            status: status message
            id: ID of newly created tile
        """

        page = Page.objects.get(pk=pk)
        tile = success = None
        status_code = 400
        
        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        obj_id = data.get('id', None)
        category = data.get('category', None)
        priority = data.get('priority', 0)
        add_type = data.get('type', None)
    
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
                    raise RuntimeError("Priority '{}' is not a number.".format(priority))
                # Check if category exists
                if category:
                    try:
                        category = Category.objects.get(name=category, store=page.store)
                    except Category.DoesNotExist:
                        raise RuntimeError("Category '{0}' not found.".format(category))
            except RuntimeError as e:
                status = str(e)
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
                            (status, tile, success) = self.add_product(filters, obj_id, page, category, priority)
                        elif add_type == 'content':
                            (status, tile, success) = self.add_content(filters, obj_id, page, category)
                        else:
                            status = "Type '{}' is not a valid type (content/product only).".format(add_type)
                    except AttributeError as e:
                        status = str(e)
                    else:
                        if success is None:
                            status_code = 400
                        elif success:
                            status_code = 200
                        else:
                            status_code = 404    
                    
        response = {
            "action": "Add",
            "status": status
        }

        if not tile == None:
            response['id'] = tile.id
            response['tile'] = TileSerializer(tile).data

        return Response(response, status=status_code)
    
    @detail_route(methods=['post'])
    def remove(self, request, pk):
        """
        Remove product or content from page

        inputs:
            id: product or content ID
            type: what type the id is: 'product' or 'content'

        returns:
            action: action performed (Remove)
            status: status message
        """

        page = Page.objects.get(pk=pk)
        success = None
        status_code = 400

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        obj_id = data.get('id', None)
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
                # Use remove_product if the type's product, else use remove_content
                try:
                    if remove_type == 'product':
                        (status, success) = self.remove_product(filters, obj_id, page)
                    elif remove_type == 'content':
                        (status, success) = self.remove_content(filters, obj_id, page)
                    else:
                        status = "Type '{}' is not a valid type (content/product only).".format(remove_type)
                except AttributeError as e:
                    status = str(e)
                else:
                    if success is None:
                        status_code = 400
                    elif success:
                        status_code = 200
                    else:
                        status_code = 404   

        return Response({
            "action": "Remove",
            "status": status,
        }, status=status_code)


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
