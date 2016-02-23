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
from apps.imageservice.utils import upload_to_cloudinary
from apps.intentrank.algorithms import ir_magic
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
            product: 
        """
        return_dict = {'status': None, 'ids': [], 'products': []}
        
        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

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
                        return_dict['products'].append(ProductSerializer(p).data)
                    return_dict['status'] = " ".join(status_parts)
                    status_code = 200
                else:
                    return_dict['status'] = "Product found: ID {0}.".format(str(product.id))
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

            try:
                page = Page.objects.get(id=data['page_id'])
            except Page.DoesNotExist:
                return_dict['status'] = "Scraping has failed. Page with ID: {} not found.".format(data['page_id'])
                status_code = 404
            else:
                def process(request, page, url, options):
                    PageMaintainer(page).add(source_urls=[url], options=options)

                p = Process(target=process, args=[page, url, options])
                p.start()
                p.join()

                try:
                    product = Product.objects.get(url=url)
                except Product.DoesNotExist:
                    return_dict['status'] = "Scraping has failed. Product Not Found."
                    status_code = 404
                else:
                    return_dict['status'] = "Scraping has succeeded. Product ID: {}".format(product.id)
                    return_dict['id'] = product.id
                    return_dict['product'].append(ProductSerializer(product).data)
                    status_code = 200

        return Response(return_dict, status=status_code)


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
            content: resultant added content
        """

        return_dict = {'status': None, 'ids': [], 'contents': []}

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

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
                        return_dict['contents'].append(ContentSerializer(c).data)
                    return_dict['status'] = " ".join(status_parts)
                    status_code = 200
                else:
                    return_dict['status'] = "Content with {0}: {1} has been found.".format(key[0], str(data[key[1]]))
                    return_dict['ids'].append(content.id)       
                    return_dict['contents'].append(ContentSerializer(content).data)
                    status_code = 200

        return Response(return_dict, status=status_code)

    @list_route(methods=['post'])
    def scrape(self, request):
        """
        Upload content to cloudinary

        inputs:
            url: url from which image is uploaded

        returns:
            status: status message containing result of upload
            url: if upload successful, secure url of uploaded image on cloudinary
            image: if upload successful, image object returned by cloudinary
            error: if upload unsuccessful, error messages returned by cloudinary
        """

        return_dict = {'status': "", 'image': []}
        status_code = 400

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        if not 'url' in data:
            return_dict['status'] = "No URL found."
        else:
            try:
                img_obj = upload_to_cloudinary(data['url'])
            except Exception as e:
                return_dict['status'] = "Upload failed. Error: {}".format(str(e))
                return_dict['error'] = str(e)
            else:
                if 'error' in img_obj:
                    return_dict['status'] = "Upload failed. Error: {}".format(img_obj['error']['http_code'])
                    return_dict['error'] = img_obj['error']
                else:
                    return_dict['status'] = "Uploaded. Image URL: {}".format(img_obj['secure_url'])
                    return_dict['url'] = img_obj['secure_url']
                    return_dict['image'] = img_obj
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

        tile = None

        try:
            product = Product.objects.get(filters)
        except Product.DoesNotExist:
            status = ("Product with ID: {0}, Store: {1} has not been found. Add failed."
                      "").format(str(product_id), page.store.name)
            success = False
        except Product.MultipleObjectsReturned:
            status = ("Multiple products with ID: {0}, Store: {1} have been found. Add "
                      "failed.").format(str(product_id), page.store.name)
            raise AttributeError(status)
        else:
            if page.feed.tiles.filter(products=product, template="product"):
                status = ("Product with ID: {0}, Name: {1}, Store: {2} is already added. "
                          "Add failed.").format(str(product_id),product.name,page.store.name)
                raise AttributeError(status)
            else:
                (tile, result) = page.feed.add(product,priority=priority,category=category)
                if result:
                    status = "Product with ID: {0}, Name: {1} has been added.".format(str(product_id), product.name)
                    success = True
                else:
                    status = ("Adding of product with ID: {0}, Name: {1} has failed due to "
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
            status = ("Product with ID: {0}, Store: {1} has not been found. "
                      "Remove failed.").format(str(product_id), page.store.name)
            success = False
        except Product.MultipleObjectsReturned:
            status = ("Multiple products with ID: {0}, Store: {1} have been found. "
                      "Remove failed.").format(str(product_id), page.store.name)
            raise AttributeError(status)
        else:
            query = Q(products=product, template="product")
            if category:
                query &= Q(categories=category)
            if not page.feed.tiles.filter(query):
                status = ("Product with ID: {0}, Name: {1}, Store: {2} has not been "
                          "found. Remove failed.").format(str(product_id), product.name, page.store.name)
                raise AttributeError(status)
            else:
                page.feed.remove(product, category=category)
                status = "Product with ID: {0}, Name: {1} has been removed.".format(str(product_id), product.name)
                success = True

        return (status, success)

    def add_content(self, filters, content_id, page, category=None, priority=None):
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
            status = ("Content with ID: {0}, Store: {1} has not been found. Add "
                      "failed.").format(str(content_id), page.store.name)
            success = False
        except Content.MultipleObjectsReturned:
            status = ("Multiple contents with ID: {0}, Store: {1} have been found. "
                      "Add failed.").format(str(content_id), page.store.name)
            raise AttributeError(status)
        else:
            #Content adding
            if page.feed.tiles.filter(content=content):
                status = ("Content with ID: {0}, Store: {1} is already added. Add "
                          "failed.").format(str(content_id), page.store.name)
                raise AttributeError(status)
            else:
                (tile, result) = page.feed.add(content,priority=priority,category=category) 
                if result:
                    status = "Content with ID: {0} has been added.".format(str(content_id))
                    success = True
                else:
                    status = ("Adding of content with ID: has failed due to an unknown "
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
            status = ("Content with ID: {0}, Store: {1} has not been found. Remove "
                      "failed.").format(str(content_id), page.store.name)
            success = False
        except Content.MultipleObjectsReturned:
            status = ("Multiple contents with ID: {0}, Store: {1} have been found. "
                      "Remove failed.").format(str(content_id), page.store.name)
            raise AttributeError(status)
        else:
            #Content removing
            query = Q(content=content)
            if category:
                query &= Q(categories=category)
            if not page.feed.tiles.filter(query):
                status = ("Content with ID: {0}, Store: {1} has not been found. "
                          "Remove failed.").format(str(content_id), page.store.name)
                raise AttributeError(status)
            else:
                page.feed.remove(content, category=category)
                status = "Content with ID: {0} has been removed.".format(str(content_id))
                success = True
        
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
            status: status message
            id: ID of newly created tile
        """

        tile = None
        
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
                            raise RuntimeError("Category '{0}' not found for store '{1}'.".format(category, page.store.name))
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
                                (status, tile, success) = self.add_content(filters, obj_id, page, category, priority)
                            else:
                                raise AttributeError("Type '{}' is not a valid type (content/product only).".format(add_type))
                        except AttributeError as e:
                            status = str(e)
                        else:
                            if success:
                                status_code = 200
                            else:
                                status_code = 404   
   
        response = {
            "status": status
        }

        if tile:
            response['id'] = tile.id
            response['tile'] = TileSerializer(tile).data 
                 
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
                                raise RuntimeError("Category '{0}' not found for store '{1}'.".format(category, page.store.name))
                    except RuntimeError as e:
                        status = str(e)
                    else:               
                        # Use remove_product if the type's product, else use remove_content
                        try:
                            if remove_type == 'product':
                                (status, success) = self.remove_product(filters, obj_id, page, category)
                            elif remove_type == 'content':
                                (status, success) = self.remove_content(filters, obj_id, page, category)
                            else:
                                raise AttributeError("Type '{}' is not a valid type (content/product only).".format(remove_type))
                        except AttributeError as e:
                            status = str(e)
                        else:
                            if success:
                                status_code = 200
                            else:
                                status_code = 404   

        return Response({
            "status": status,
        }, status=status_code)


class TileViewSet(viewsets.ModelViewSet):
    queryset = Tile.objects.all()
    serializer_class = TileSerializer

    @list_route(methods=['post'])
    def edit_single_priority(self, request):
        """
        Edit the priority of a single tile

        inputs:
            tile_id: ID of tile
            priority: new priority

        returns:
            status: status message
        """

        return_dict = {'status': None}
        status_code = 400

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        if not 'tile_id' in data:
            return_dict['status'] = "Missing 'tile_id' field from input."
        elif not 'priority' in data:
            return_dict['status'] = "Missing 'priority' field from input."
        else:
            try:
                tile_id = int(data['tile_id'])
                priority = int(data['priority'])
            except (TypeError, ValueError):
                return_dict['status'] = "Expecting a number as input, but got non-number."
            else:
                try:
                    tile = Tile.objects.get(pk=tile_id)
                except Tile.DoesNotExist:
                    return_dict['status'] = "The tile with ID: {0} could not be found.".format(tile_id)
                    status_code = 404
                else:
                    if priority == tile.priority:
                        return_dict['status'] = "The priority of the tile with ID: {0} is already {1}.".format(tile_id, priority)
                    else:
                        tile.priority = priority
                        tile.save()
                        return_dict['status'] = "The priority of the tile with ID: {0} has been changed to {1}.".format(tile_id, priority)
                        status_code = 200

        return Response(return_dict, status=status_code)

    def check_ordered(self, tileList):
        """
        Check if the list given is ordered.
        Ordered tile lists have a decreasing priority count, such that 
            tileList[x].priority = tileList[x+1].priority + 1

        input:
            tileList: list of all tiles

        returns:
            True/False: True if the list is ordered, False otherwise
        """

        ordered = True
        for x in range(0,len(tileList)-2):
            if not tileList[x].priority == tileList[x+1].priority + 1:
                ordered = False
                break
        return ordered

    def set_increasing_priority(self, tileList, ind):
        """
        Set the priority of tiles inside the tileList to be decreasing starting from
            index of 0 up to the specified index

        inputs:
            tileList: list of all tiles
            ind: stopping tile index

        returns:
            tileList: tileList after setting priorities of tiles 
        """

        for t in range(ind, -1, -1):
            tileList[t].priority = tileList[t+1].priority + 1
            tileList[t].save()

        return tileList


    def swap_ordered_priorities(self, tileList, tile1_ind, tile2_ind):
        """
        Swap the location of 2 tiles an ordered tile list.
        Ordered tile lists have a decreasing priority count, such that 
            tileList[x].priority = tileList[x+1].priority + 1
        Swapping ordered tile lists require simply exchanging the priorities of 
            the two tiles that needs to be swapped

        inputs:
            tileList: list of all tiles
            tile1_ind: index of tile 1 in list of all tiles
            tile2_ind: index of tile 2 in list of all tiles

        returns:
            tileList: tileList after swapping
        """

        # Swap the priority of the tiles in the tileList
        temp = tileList[tile1_ind].priority
        tileList[tile1_ind].priority = tileList[tile2_ind].priority
        tileList[tile2_ind].priority = temp
        
        # Swap the tiles in the tileList
        temp = tileList[tile1_ind]
        tileList[tile1_ind] = tileList[tile2_ind]
        tileList[tile2_ind] = temp

        tileList[tile1_ind].save()
        tileList[tile2_ind].save()
        return tileList

    def swap_unordered_priorities(self, tileList, tile1_ind, tile2_ind):
        """
        Swap the location of 2 tiles an unordered tile list.
        Ordered tile lists have a decreasing priority count, such that 
            tileList[x].priority = tileList[x+1].priority + 1
        Swapping unordered tile lists require setting the priority of all tiles
            from index of 0 to tile2_ind

        inputs:
            tileList: list of all tiles
            tile1_ind: index of tile 1 in list of all tiles
            tile2_ind: index of tile 2 in list of all tiles

        returns:
            tileList: tileList after swapping
        """

        tile1 = tileList[tile1_ind]
        tile2 = tileList[tile2_ind]
        # Make sure that tile1_ind is the tile on the left, tile1_ind is the tile on the right
        if tile1_ind > tile2_ind:
            temp = tile1_ind
            tile1_ind = tile2_ind
            tile2_ind = temp

        # Swap Tile1 and Tile2 in list
        temp = tileList[tile1_ind]
        tileList[tile1_ind] = tileList[tile2_ind]
        tileList[tile2_ind] = temp

        temp = tile1_ind
        tile1_ind = tile2_ind
        tile2_ind = temp

        # Tile1 is now swapped with Tile2, so just need to set priorities. Tile1 is now on the right, Tile2 is on left

        # Set tile1's priority to the one 1 to the right's +1
        if tile1_ind == len(tileList) - 1:
            # This means tile1 is now at the end of the list so just set priority = 1
            tileList[tile1_ind].priority = 1
        else:
            # This means tile1 is not at the end of the list so there are still things on the right of it
            tileList[tile1_ind].priority = tileList[tile1_ind + 1].priority + 1

        tileList[tile1_ind].save()

        # Now just loop from tile1 to tile with ind of 0 in list, while setting priority + 1 the next one
        tileList = self.set_increasing_priority(tileList, tile1_ind-1)

        return tileList

    @list_route(methods=['post'])
    def swap_tile_location(self, request):
        """
        Swap the location of 2 tiles on a page

        inputs:
            tile_id1: ID of tile 1
            tile_id2: ID of tile 2
            page_id: page that contains both tiles to be swapped

        returns:
            status: status message
        """

        return_dict = {'status': None}
        status_code = 400

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        if not 'tile_id1' in data:
            return_dict['status'] = "Missing 'tile_id1' field from input."
        elif not 'tile_id2' in data:
            return_dict['status'] = "Missing 'tile_id2' field from input."
        elif not 'page_id' in data:
            return_dict['status'] = "Missing 'page_id' field from input."
        else:
            try:
                tile_id1 = int(data['tile_id1'])
                tile_id2 = int(data['tile_id2'])
                page_id = int(data['page_id'])

                if tile_id1 == tile_id2:
                    raise AttributeError
            except (TypeError, ValueError):
                return_dict['status'] = "Expecting a number as input, but got non-number."
            except AttributeError:
                return_dict['status'] = "'tile_id1' cannot be equal to 'tile_id2'."
            else:
                try:
                    page = Page.objects.get(pk=page_id)
                    page_tiles = page.feed.tiles
                except Page.DoesNotExist:
                    return_dict['status'] = "The page with ID: {0} could not be found.".format(page_id)
                except AttributeError:
                    return_dict['status'] = "The page with ID: {0} does not have a feed or the feed has no tiles.".format(page_id)
                else:
                    try:
                        tile1 = Tile.objects.get(pk=tile_id1)
                        if not tile1 in page_tiles.all():
                            raise ValueError
                    except Tile.DoesNotExist:
                        return_dict['status'] = "The tile with ID: {0} could not be found.".format(tile_id1)
                    except ValueError:
                        return_dict['status'] = "The tile with ID: {0} is not part of the page with ID: {1}.".format(tile_id1,page_id)
                    else:
                        try:
                            tile2 = Tile.objects.get(pk=tile_id2)
                            if not tile2 in page_tiles.all():
                                raise ValueError
                        except Tile.DoesNotExist:
                            return_dict['status'] = "The tile with ID: {0} could not be found.".format(tile_id2)
                        except ValueError:
                            return_dict['status'] = "The tile with ID: {0} is not part of the page with ID: {1}.".format(tile_id2,page_id)
                        else:
                            tileMagic = list(ir_magic(page_tiles, num_results=page_tiles.count()))
                            ordered = self.check_ordered(tileMagic)

                            tile1_ind = tileMagic.index(tile1)
                            tile2_ind = tileMagic.index(tile2)

                            if ordered:
                                tileMagic = self.swap_ordered_priorities(tileMagic, tile1_ind, tile2_ind)
                            else:
                                tileMagic = self.swap_unordered_priorities(tileMagic, tile1_ind, tile2_ind)

                            return_dict['status'] = "The tile with ID: {0} has been swapped with tile with ID: {1}.".format(tile_id1, tile_id2)
                            status_code = 200

        return Response(return_dict, status=status_code)

    @list_route(methods=['post'])
    def move_tile_to_position(self, request):
        """
        Move the tile to index position

        inputs:
            index: index to move tile to, with index = 0 indidcating 1st item of list of tiles
            tile_id: ID of tile
            page_id: page that contains tile to be moved

        returns:
            status: status message
        """

        return_dict = {'status': None}
        status_code = 400

        try:
            data = request.POST or ast.literal_eval(request.body)
        except SyntaxError:
            data = {}

        if not 'index' in data:
            return_dict['status'] = "Missing 'index' field from input."
        elif not 'tile_id' in data:
            return_dict['status'] = "Missing 'tile_id' field from input."
        elif not 'page_id' in data:
            return_dict['status'] = "Missing 'page_id' field from input."
        else:
            try:
                index = int(data['index'])
                tile_id = int(data['tile_id'])
                page_id = int(data['page_id'])
            except (TypeError, ValueError):
                return_dict['status'] = "Expecting a number as input, but got non-number."
            else:
                try:
                    page = Page.objects.get(pk=page_id)
                    page_tiles = page.feed.tiles
                except Page.DoesNotExist:
                    return_dict['status'] = "The page with ID: {0} could not be found.".format(page_id)
                except AttributeError:
                    return_dict['status'] = "The page with ID: {0} does not have a feed or the feed has no tiles.".format(page_id)
                else:
                    try:
                        tile = Tile.objects.get(pk=tile_id)
                        if not tile in page_tiles.all():
                            raise ValueError
                        tileMagic = list(ir_magic(page_tiles, num_results=page_tiles.count()))
                        tile_index = tileMagic.index(tile)
                        if tile_index == index:
                            raise AttributeError()
                        if index >= page_tiles.count() or index < 0:
                            raise IndexError
                    except Tile.DoesNotExist:
                        return_dict['status'] = "The tile with ID: {0} could not be found.".format(tile_id)
                    except ValueError:
                        return_dict['status'] = "The tile with ID: {0} is not part of the page with ID: {1}.".format(tile_id, page_id)
                    except AttributeError:
                        return_dict['status'] = "The tile with ID: {0} is already at index {1}.".format(tile_id, index)
                    except IndexError:
                        return_dict['status'] = "The index {} is out of range of the tile list.".format(index)
                    else:
                        # Now we need to make the new list so we can reorder the tiles using priority
                        # First check if the index we're moving to is on the left or right of original tile index
                        # Then insert/delete appropriately
                        if index < tile_index:
                            tileMagic.insert(index, tileMagic[tile_index])  
                            del tileMagic[tile_index+1]
                        else:
                            tileMagic.insert(index+1, tileMagic[tile_index])  
                            del tileMagic[tile_index]

                        # Set the starting point for re-numbering the priority to be the one on the right most
                        if index > tile_index:
                            start_point = index
                        else:
                            start_point = tile_index

                        if start_point == len(tileMagic) - 1:
                            # This means the starting point is now at the end of the list so just set priority = 1
                            tileMagic[start_point].priority = 1
                        else:
                            # This means the starting point is not at the end of the list so just set priority = element on the right + 1
                            # This makes sure that the starting point will always be at this spot
                            tileMagic[start_point].priority = tileMagic[start_point + 1].priority + 1

                        tileMagic[start_point].save()

                        # Go from starting point to the beginning of the list, while setting the priorities for each tile
                        tileMagic = self.set_increasing_priority(tileMagic, start_point-1)

                        return_dict['status'] = "The tile with ID: {0} has been moved to index {1}.".format(tile_id, index)
                        status_code = 200

        return Response(return_dict, status=status_code)

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
