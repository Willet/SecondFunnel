import json
import re

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.db import models
from jsonfield import JSONField

import apps.api.serializers as cg_serializers
import apps.intentrank.serializers as ir_serializers
from apps.utils import returns_unicode

from .core import BaseModel
#from .elements import Product, Content # deferred to end of file

"""
Store -> Page -> Theme
     |        -> Feed -> Tile
      -> Category --------^
"""

class Store(BaseModel):
    """
    All other models exist under a store and should never be re-assigned.

    All other models under a store should cascade delete on store deletion
    """
    staff = models.ManyToManyField(User, related_name='stores')

    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    slug = models.CharField(max_length=64)

    default_theme = models.ForeignKey('Theme', related_name='store', blank=True,
                                      null=True, on_delete=models.SET_NULL)
    default_page = models.ForeignKey('Page', related_name='default_store', blank=True,
                                     null=True, on_delete=models.SET_NULL)

    public_base_url = models.URLField(
        help_text="e.g. http://explore.nativeshoes.com, used for store detection",
        blank=True, null=True)

    serializer = ir_serializers.StoreSerializer
    cg_serializer = cg_serializers.StoreSerializer

    @classmethod
    def from_json(cls, json_data):
        """@deprecated for replacing the Campaign Model. Use something else.
        """
        if 'theme' in json_data:
            json_data['theme'] = Theme(template=json_data['theme'])

        instance = cls()
        for field in json_data:
            setattr(instance, field, json_data[field])
        return instance


class Theme(BaseModel):
    """
    :attr template either a local path or a remote path, e.g.
        "apps/pinpoint/templates/pinpoint/campaign_base.html"
        "apps/pinpoint/static/pinpoint/themes/gap/index.html"
        "https://static-misc-secondfunnel/themes/campaign_base.html"
    """
    name = models.CharField(max_length=1024, blank=True, null=True)
    template = models.CharField(
        max_length=1024,
        # backward compatibility for pages that don't specify themes
        default="apps/pinpoint/templates/pinpoint/campaign_base.html")

    @returns_unicode
    def load_theme(self):
        """download/open the template as a string."""
        from apps.light.utils import read_a_file, read_remote_file

        if 'static-misc-secondfunnel/themes/gap.html' in self.template:
            # exception for task "Get all pages on tng-test and tng-master using gap theme as code"
            self.template = 'apps/pinpoint/static/pinpoint/themes/gap/index.html'

        local_theme = read_a_file(self.template, '')
        if local_theme:
            return local_theme

        remote_theme = read_remote_file(self.template, '')[0]
        if remote_theme:
            print "[INFO] speed up page load times by placing the theme" \
                  " '{0}' locally.".format(self.template)
            return remote_theme

        print "[WARN] template '{0}' was neither local nor remote".format(
            self.template)
        return self.template


class Page(BaseModel):
    """
    Controls the source of the page content & how the page should look / behave

    Store -> Page -> Feed
    """
    store = models.ForeignKey('Store', related_name='pages', on_delete=models.CASCADE)

    name = models.CharField(max_length=256)  # e.g. Lived In
    theme = models.ForeignKey('Theme', related_name='pages', blank=True, null=True)
            #on_delete=models.SET_NULL,

    # attributes named differently
    theme_settings = JSONField(default=lambda:{}, blank=True, null=True)

    theme_settings_fields = [
        ('image_tile_wide', 0.0),
        ('desktop_hero_image', ''),
        ('mobile_hero_image', ''),
        ('column_width', 256),
        ('social_buttons', []),
        ('enable_tracking', "true"),
    ]

    dashboard_settings = JSONField(default=lambda:{}, blank=True)
    campaign = models.ForeignKey('dashboard.Campaign', blank=True, null=True)
               #on_delete=models.SET_NULL,

    description = models.TextField(blank=True, null=True)
    url_slug = models.CharField(max_length=128)  # e.g. livedin
    legal_copy = models.TextField(blank=True, null=True)

    last_published_at = models.DateTimeField(blank=True, null=True)

    feed = models.ForeignKey('Feed', related_name='page', blank=True, null=True) 

    _attribute_map = BaseModel._attribute_map + (
        # (cg attribute name, python attribute name)
        ('social-buttons', 'social_buttons'),
        ('column-width', 'column_width'),
        ('intentrank-id', 'intentrank_id'),
        ('heroImageDesktop', 'desktop_hero_image'),
        ('heroImageMobile', 'mobile_hero_image'),
        ('legalCopy', 'legal_copy'),  # ordered for cg -> sf
        ('description', 'description'),  # ordered for cg -> sf
        ('shareText', 'description'),  # ordered for cg <- sf
    )

    serializer = ir_serializers.PageSerializer
    cg_serializer = cg_serializers.PageSerializer

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # self._theme_settings is a merged theme_settings with defaults
        if not self.theme_settings:
            self._theme_settings = { key: default for (key, default) in self.theme_settings_fields }
        else:
            self._theme_settings = self.theme_settings.copy()
            for (key, default) in self.theme_settings_fields:
                if not key in self.theme_settings:
                    self._theme_settings[key] = default

    def __getattr__(self, name):
        try:
            # Need to use parent __getattribute__ to avoid infinite loop
            return super(self.__class__, self).__getattribute__('_theme_settings')[name]
        except (AttributeError, KeyError):
            return super(self.__class__, self).__getattribute__(name)

    def __copy__(self):
        """Duplicates the page, points to existing feed & associated tiles
        returns: page"""
        return self.__class__._copy(self, update_fields= {'url_slug': self._get_incremented_url_slug()})

    def __deepcopy__(self, memo={}):
        """Duplicates the page, feed & associated tiles
        returns: page"""
        feed = self.feed.deepcopy()
        feed.save() # ensure feed is saved
        return self.__class__._copy(self, update_fields= {'url_slug': self._get_incremented_url_slug(),
                                                          'feed': feed })

    def copy(self):
        """page.copy() is alias for copy(page)"""
        return self.__copy__()

    def deepcopy(self):
        """page.deepcopy() is alias for deepcopy(page)"""
        return self.__deepcopy__()

    def deepdelete(self):
        """Attempts to delete all database elements associated with this page iff
           those elements are not associated with any other page:
           - Feed (if only associated with this page)
           - Tiles (if associated with Feed)
           - Products (if only tagged in Tiles to be deleted)
           - Contents (if only tagged in Tiles to be deleted)

        :returns bool - True if deleted Feed & related items, False if only deleted Page
        """
        if not self.feed:
            self.delete()
            return False
        elif self.feed.page.count() > 1:
            # This Feed is associated with other pages, can't deep delete
            self.delete()
            return False
        else:
            # Get all product tiles & content tiles
            self.feed.deepdelete() # Will remove tiles too
            self.delete()
            return True

    def replace(self, page, deepdelete=False):
        """Replaces page with self (assuming its url_slug) & deletes page.  If the feed
        is only related to this page, it is deleted too.

        If deepdelete, then deepdelete page & feed.

        :returns bool - True if deleted Feed & related items, False if only deleted Page
        """
        self.url_slug = page.url_slug
        if deepdelete:
            return page.deepdelete()
        else:
            if page.feed.page.count() == 1:
                page.feed.delete()
            page.delete()
            return False
        self.save()

    def get(self, key, default=None):
        """Duck-type a <dict>'s get() method to make CG transition easier.

        Also looks into the theme_settings JSONField if present.
        """
        try:
            return getattr(self, key)
        except AttributeError:
            pass

        if hasattr(self, 'theme_settings') and self.theme_settings:
            if key in self.theme_settings:
                return self.theme_settings.get(key, default)
        return default

    @classmethod
    def from_json(cls, json_data):
        """@deprecated for replacing the Campaign Model. Use something else.
        """
        if 'theme' in json_data:
            json_data['theme'] = Theme(template=json_data['theme'])

        instance = cls()
        for field in json_data:
            setattr(instance, field, json_data[field])
        return instance

    def _get_incremented_url_slug(self):
        """Returns the url_slug with an incremented number. Guaranteed unique url_slug
        - "url_slug_1" for "url_slug"
        - "url_slug_2" for "url_slug_1
        """
        def increment_url_slug(url_slug):
            m = re.match(r"^(.*_)(\d+)$", url_slug)
            if m:
                url_slug = m.group(1) + str(int(m.group(2)) + 1)
            else:
                url_slug += "_1"

            try:
                self.__class__.objects.get(store=self.store, url_slug=url_slug)
            except ObjectDoesNotExist:
                # url_slug unique
                pass
            else:
                # Recursively increment
                url_slug = increment_url_slug(url_slug)
            finally:
                return url_slug
        return increment_url_slug(self.url_slug)

    def _get_incremented_name(self):
        """Returns the name
        - "name COPY 1" for "name"
        - "name COPY 2" for "name COPY 1"
        """
        def increment_name(name):
            m = re.match(r"^(.* COPY )(\d+)$", name)
            if m:
                name = m.group(1) + str(int(m.group(2)) + 1)
            else:
                name += " COPY 1"

            try:
                self.__class__.objects.get(store=self.store, name=name)
            except ObjectDoesNotExist:
                # url_slug unique
                pass
            else:
                # Recursively increment
                name = increment_name(name)
            finally:
                return name
        return increment_name(self.name)

    def add(self, obj, prioritized=False, priority=0):
        """Alias for Page.feed.add
        """
        return self.feed.add(obj=obj, prioritized=prioritized,
                             priority=priority)

    def remove(self, obj):
        """Alias for Page.feed.remove
        """
        return self.feed.remove(obj=obj)


class Feed(BaseModel):
    """
    Container for tiles for a page / ad

    Page -> Feed -> Tiles

    TODO: expanding Feed's understanding of sources to be able to recreate itself
    """
    # pages = <RelatedManager> Pages (many-to-one relationship)
    # tiles = <RelatedManager> Tiles (many-to-one relationship)
    store = models.ForeignKey('Store', related_name='feeds', on_delete=models.CASCADE)
    feed_algorithm = models.CharField(max_length=64, blank=True, null=True)  # ; e.g. sorted, recommend
    feed_ratio = models.DecimalField(max_digits=2, decimal_places=2, default=0.20,  # currently only used by ir_mixed
                                     help_text="Percent of content to display on feed using ratio-based algorithm")
    is_finite = models.BooleanField(default=False)

    # Fields necessary to update / regenerate feed
    source_urls = JSONField(default=lambda:[]) # List of <str> urls feed is generated from
    spider_name = models.CharField(max_length=64, blank=True) # Spider defines behavior to update / regenerate page, '' valid

    serializer = ir_serializers.FeedSerializer

    def __unicode__(self):
        try:
            page_names = ', '.join(page.name for page in self.page.all())
            return u'Feed (#%s), pages: %s' % (self.id, page_names)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return u'Feed (#%s)' % self.id
        except:
            return u'(Unsaved Feed)'

    def __copy__(self):
        """A shallow copy of a feed does not include tiles. It is highly unlikely that that
        was the intention.  Force conscious use of deepcopy
        """
        raise NotImplementedError

    def __deepcopy__(self, memo={}):
        """Creates a duplicate of the feed & its tiles
        :returns new feed"""
        feed = self.__class__._copy(self)
        for tile in self.tiles.all():
            feed._copy_tile(tile)
        return feed

    def deepcopy(self):
        """feed.deepcopy() is alias for deepcopy(feed)"""
        return self.__deepcopy__()

    def deepdelete(self):
        """Delete the feed, its tiles, and all product & content that is not
        tagged in any other tile"""
        self._deepdelete_tiles(self.tiles.select_related('products','content').all())
        self.delete() # Cascades to tiles

    def clear_category(self, category, deepdelete=False):
        """Delete all feed tiles tagged only with category

        :param tag - can be str (name field of category) or Category instance

        :option deepdelete - if True, delete all product & content that is not tagged
        in any other tile
        """
        category = category if isinstance(category, Category) else Category.objects.get(name=category)
        if deepdelete:
            tiles = self.tiles.select_related('products','content').filter(categories__in=[category])
            self._deepdelete_tiles(tiles)
        else:
            self.tiles.filter(categories__in=[category]).delete()

    def find_tiles(self, content=None, product=None):
        """:returns list of tiles with this product/content (if given)"""
        if content:
            return self.tiles.filter(content__id=content.id)
        elif product:
            return self.tiles.filter(products__id=product.id)
        else:
            return self.tiles.all()

    def get_in_stock_tiles(self):
        return self.tiles.exclude(products__in_stock=False)\
            .exclude(content__tagged_products__in_stock=False)

    def add(self, obj, prioritized=u"", priority=0, force_create_tile=False):
        """ Add a <Product>, <Content> as a new tile, or copy an existing <Tile> to the feed. If the
        Product already exists as a product tile, or the Content exists as a content tile, updates
        and returns that tile

        If force_create_tile is True, forces the creation of a new tile

        :returns <Tile>, <bool> created

        :raises ValueError"""
        if isinstance(obj, Product):
            return self._add_product(product=obj, prioritized=prioritized,
                                     priority=priority, force_create_tile=force_create_tile)
        elif isinstance(obj, Content):
            return self._add_content(content=obj, prioritized=prioritized,
                                     priority=priority, force_create_tile=force_create_tile)
        elif isinstance(obj, Tile):
            tile = self._copy_tile(tile=obj, prioritized=prioritized,
                                     priority=priority)
            return (tile, True)
        raise ValueError("add() accepts either Product, Content or Tile; "
                         "got {}".format(obj.__class__))

    def remove(self, obj, deepdelete=False):
        """:raises ValueError"""
        if isinstance(obj, Product):
            return self._remove_product(product=obj, deepdelete=deepdelete)
        elif isinstance(obj, Content):
            return self._remove_content(content=obj, deepdelete=deepdelete)
        elif isinstance(obj, Tile):
            return self._deepdelete_tiles(tiles=self.tiles.get(id=obj.id)) if deepdelete else obj.delete()
        raise ValueError("remove() accepts either Product, Content or Tile; "
                         "got {}".format(obj.__class__))

    def get_all_products(self, pk_set=False):
        """Gets all tagged, related & similar products to this feed. Useful for bulk updates

        pk_set (bool): if True, return a set of primary keys

        :returns <QuerySet> of products"""
        product_pks = set()

        # Get ALL the products associated with this page
        for tile in self.tiles.all():
            for product in tile.products.all():
                product_pks.add(product.pk)
                if product.similar_products:
                    product_pks.update(product.similar_products.values_list('pk', flat=True))
            for content in tile.content.all():
                if content.tagged_products:
                    product_pks.update(content.tagged_products.values_list('pk', flat=True))
        if pk_set:
            return product_pks
        else:
            return Product.objects.filter(pk__in=product_pks).all()

    def _copy_tile(self, tile, prioritized=False, priority=0):
        """Creates a copy of a tile to this feed

        :returns <Tile> copy"""
        new_tile = Tile._copy(tile, update_fields= {'feed': self,
                                                    'prioritized': prioritized or tile.prioritized,
                                                    'priority': priority if isinstance(priority, int) else tile.priority })
        new_tile.save()

        return new_tile

    def _deepdelete_tiles(self, tiles):
        """Tiles is a <QuerySet> (ex: Feed.tiles.objects.all())

        TODO: incorporate tagged products & similar products"""
        tiles_set = set(tiles.values_list('pk', flat=True))
        bulk_delete_products = []
        bulk_delete_content = []

        for tile in tiles:
            # Queue products & content for deletion if they are ONLY tagged in
            # Tiles that will be delete
            for p in tile.products.all():
                if set(p.tiles.values_list('pk', flat=True)).issubset(tiles_set):
                    bulk_delete_products.append(p.pk)
            for c in tile.content.all():
                if set(c.tiles.values_list('pk', flat=True)).issubset(tiles_set):
                    bulk_delete_content.append(c.pk)

        Product.objects.filter(pk__in=bulk_delete_products).delete()
        Content.objects.filter(pk__in=bulk_delete_content).delete()

        tiles.delete()

    def _add_product(self, product, prioritized=u"", priority=0, force_create_tile=False):
        """Adds (if not present) a tile with this product to the feed.

        If force_create_tile is True, will create a new tile even an existing product tile exists

        :returns tuple (the tile, the product, whether it was newly added)
        :raises AttributeError, ValidationError
        """
        if not force_create_tile:
            # Check for existing tile
            existing_tiles = self.tiles.filter(products__id=product.id, template='product')
            if len(existing_tiles):
                tile = existing_tiles[0]
                tile.prioritized = prioritized
                tile.priority = priority
                tile.save() # Update IR Cache
                print "<Product {0}> already in the feed. Updated <Tile {1}>.".format(product.id, tile.id)
                return (tile, False)

        # Create new tile
        new_tile = self.tiles.create(feed=self,
                                     template='product',
                                     prioritized=prioritized,
                                     priority=priority)
        new_tile.products.add(product)
        new_tile.save()
        print "<Product {0}> added to the feed in <Tile {1}>.".format(product.id, new_tile.id)

        return (new_tile, True)

    def _add_content(self, content, prioritized=u"", priority=0, force_create_tile=False):
        """Adds (if not present) a tile with this content to the feed.

        If force_create_tile is True, will create a new tile even an existing content tile exists

        :returns tuple (the tile, the content, whether it was newly added)
        :raises AttributeError, ValidationError
        """
        if not force_create_tile:
            # Check for existing tile
            existing_tiles = self.tiles.filter(content__id=content.id)
            if len(existing_tiles):
                # Update tile
                # Could attempt to be smarter about choosing the most appropriate tile to update
                # It would have just the 1 piece of content
                tile = existing_tiles[0]
                tile.prioritized = prioritized
                tile.priority = priority
                product_qs = content.tagged_products.all()
                tile.products.add(*product_qs)
                tile.save()
                print "<Content {0}> already in the feed. Updated <Tile {1}>".format(content.id, tile.id)
                return (tile, False)

        # Create new tile
        new_tile = self.tiles.create(feed=self,
                                     template='image',
                                     prioritized=prioritized,
                                     priority=priority)

        # content template adjustments. should probably be somewhere else
        if isinstance(content, Video):
            if 'youtube' in content.url:
                new_tile.template = 'youtube'
            else:
                new_tile.template = 'video'

        new_tile.content.add(content)
        product_qs = content.tagged_products.all()
        new_tile.products.add(*product_qs)
        new_tile.save()
        print "<Content {0}> added to the feed. Created <Tile {1}>".format(content.id, new_tile.id)
        return (new_tile, True)

    def _remove_product(self, product, deepdelete=False):
        """Removes (if present) product tiles with this product from the feed.

        If deepdelete, product will be deleted too (wiping tagging associations)

        :raises AttributeError
        """
        tiles = self.tiles.filter(products__id=product.id, template='product')
        self._deepdelete_tiles(tiles) if deepdelete else tiles.delete()

    def _remove_content(self, content, deepdelete=False):
        """Removes (if present) tiles with this content from the feed that
        belongs to this page.

        If deepdelete, tries to delete other products & content associated with
        this content (will not delete them if they are in other tiles.

        :raises AttributeError
        """
        tiles = self.tiles.filter(content__id=content.id)
        self._deepdelete_tiles(tiles) if deepdelete else tiles.delete()


class Category(BaseModel):
    """ Feed category, shared name across all feeds for a store

    Store -> Category -> Tiles

    # To filter a feed by category:
    category_tiles = Feed.tiles.objects.filter(categories__id=category)

    # To add tiles to a category, filter with the Store
    Category.objects.get(name=cat_name, store=store)
    """
    tiles = models.ManyToManyField('Tile', related_name='categories')
    store = models.ForeignKey(Store, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    url = models.TextField(blank=True, null=True)

    def full_clean(self):
        kwargs = {
            'store': self.store,
            'name__iexact': self.name, # django field lookup "iexact", meaning: ignore case
        }
        # Make sure there aren't multiple Category's with the same name for this store
        try:
            cat = Category.objects.get(**kwargs)
        except Category.DoesNotExist:
            # First of its kind, ok
            pass
        except Category.MultipleObjectsReturned:
            # Already multiples, bail!
            raise ValueError("Category's must have a unique name for each store")
        else:
            # Only one, make it sure its this one
            if not self.pk == cat.pk:
                raise ValueError("Category's must have a unique name for each store")
        return


class Tile(BaseModel):
    """
    A unit in a feed, defined by a template, product(s) and content(s)

    ir_cache is updated with every tile save.  See tile_saved task

    Feed -> Tile -> Products / Content
    """
    def _validate_prioritized(status):
        allowed = ["", "request", "pageview", "session", "cookie", "custom"]
        if type(status) == bool:
            status = "pageview" if status else ""
        if status not in allowed:
            raise ValidationError("{0} is not an allowed status; "
                                  "choices are {1}".format(status, allowed))
        return status

    # <Feed>.tiles.all() gives you... all its tiles
    feed = models.ForeignKey('Feed', related_name='tiles', on_delete=models.CASCADE)

    # Universal templates: 'product', 'image', 'banner', 'youtube'
    # Invent templates as needed
    template = models.CharField(max_length=128)

    products = models.ManyToManyField('Product', blank=True, null=True,
                                      related_name='tiles')
    # use content.select_subclasses() instead of content.all()!
    content = models.ManyToManyField('Content', blank=True, null=True,
                                     related_name='tiles')
    # categories = <RelatedManager> Category (many-to-one relationship)

    # '': not prioritized.
    # 'request': prioritized for every IR request made by the client.
    # 'pageview': prioritized for every page view made by the client. (implemented in some algorithms, see docs)
    # 'session': prioritized for the beginning of each session.
    # 'cookie': prioritized if the tile cookie does not exist. (not implemented)
    # 'custom': run the tile's priority function that returns an int.
    #           the tile will be as prioritized within the feed as the size
    #           of that int. (not implemented)
    prioritized = models.CharField(
        max_length=255, default="", blank=True,
        null=True, validators=[_validate_prioritized])

    # if the feed's algorithm is 'generic', then priority is not used.
    # if the feed's algorithm is 'ordered', then prioritized tiles will be
    # sorted using this attribute instead of the tile's created date.
    #   negative values are allowed.
    #   identical values are shuffled.
    priority = models.IntegerField(null=True, default=0)

    # miscellaneous attributes, e.g. "is_banner_tile"
    attributes = JSONField(blank=True, null=True, default=lambda:{})

    clicks = models.PositiveIntegerField(default=0)

    views = models.PositiveIntegerField(default=0)

    cg_serializer = cg_serializers.TileSerializer

    def _copy(self, *args, **kwargs):
        # Should only be able to copy if new feed & feed belong to same store
        try:
            destination_feed = kwargs['update_fields']['feed']
        except KeyError:
            pass
        else:
            if not self.store.pk == destination_feed.store.pk:
                raise ValueError("Can not copy tile to feed belonging to a different store")
        
        return super(Tile, self)._copy(*args, **kwargs)

    def clean(self):
        # TODO: move m2m validation into a pre-save signal (see tasks.py)
        if self.products.exclude(store__id=self.feed.store.id).count():
            raise ValidationError({'products': 'Products may not be from a different store'})
        if self.content.exclude(store__id=self.feed.store.id).count():
            raise ValidationError({'products': 'Content may not be from a different store'})

    def deepdelete(self):
        bulk_delete_products = []
        bulk_delete_content = []

        # Queue products & content for deletion if they are ONLY tagged in
        # this single Tile
        for p in tile.products.all():
            if p.tiles.count() == 1:
                bulk_delete_products.append(p)
        for c in tile.content.all():
            if c.tiles.count() == 1:
                bulk_delete_content.append(c)
        Product.objects.filter(pk__in=bulk_delete_products).delete()
        Content.objects.filter(pk__in=bulk_delete_content).delete()

        self.delete()

    def full_clean(self, exclude=None, validate_unique=True):
        # south turns False into string 'false', which isn't what we wanted.
        # this turns 'true' and 'false' into appropriate priority flags.
        if type(self.prioritized) == bool:
            self.prioritized = 'pageview' if self.prioritized else ''
        if self.prioritized == 'true':
            self.prioritized = 'pageview'
        if self.prioritized in [0, '0', 'false']:
            self.prioritized = ''
        return super(Tile, self).full_clean(exclude=exclude,
                                            validate_unique=validate_unique)

    def to_json(self, skip_cache=False):
        return json.loads(self.to_str(skip_cache=skip_cache))

    def to_str(self, skip_cache=False):
        # determine what kind of tile this is
        serializer = None
        try:
            target_class = self.template.capitalize()
            serializer = getattr(ir_serializers,
                                 '{}TileSerializer'.format(target_class))
        except AttributeError:  # cannot find e.g. 'Youtube'TileSerializer -- use default
            serializer = ir_serializers.TileSerializer
        
        return serializer().to_str([self], skip_cache=skip_cache)

    @property
    def tile_config(self):
        """(read-only) representation of the tile as its content graph
        tileconfig."""
        return cg_serializers.TileConfigSerializer.dump(self)

    @property
    def product(self):
        """Returns the tile's first product, or the first tagged product from
        the tile's first piece of content that has tagged products.
        """
        if self.products.count():
            return self.products.all()[0]
        for content in self.content.all():
            if content.tagged_products.count():
                return content.tagged_products.all()[0]

        return None


# Circular import
from .elements import Product, Content
