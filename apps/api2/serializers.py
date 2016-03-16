from rest_framework import serializers
from rest_framework_bulk import BulkListSerializer, BulkSerializerMixin
from django.contrib.auth.models import User

from apps.assets.models import Store, Product, Content, Image, Gif, ProductImage, Video, Page, Tile, Feed, Category

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'staff', 'name', 'description', 'slug', 'display_out_of_stock', 'default_theme',
            'default_page', 'public_base_url')

class ProductSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Product
        fields = ('id', 'store', 'name', 'description', 'details', 'url', 'sku', 'price', 'sale_price', 
            'currency', 'default_image', 'last_scraped_at', 'in_stock', 'attributes', 'similar_products')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'url', 'original_url', 'file_type', 'file_checksum', 'width', 'height', 
            'dominant_color', 'image_sizes', 'attributes')

class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ('id', 'store', 'name', 'description', 'url', 'source', 'source_url', 'tagged_products', 
            'attributes', 'status')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'file_type', 'file_checksum', 'width', 'height', 'dominant_color', 'store',
            'name', 'description', 'url', 'source', 'source_url', 'tagged_products', 'attributes', 'status')

class GifSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gif
        fields = ('id', 'gif_url', 'file_type', 'file_checksum', 'width', 'height', 'dominant_color',
            'store', 'name', 'description', 'url', 'source', 'source_url', 'tagged_products',
            'attributes', 'status')

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('id', 'player', 'file_type', 'file_checksum', 'original_id', 'store', 'name',
            'description', 'url', 'source', 'source_url', 'tagged_products', 'attributes', 'status')

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('id', 'store', 'name', 'theme', 'theme_settings', 'dashboard_settings', 'campaign', 
            'description', 'url_slug', 'legal_copy', 'last_published_at', 'feed')

class TileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tile
        fields = ('id', 'feed', 'template', 'products', 'content', 'priority', 'clicks', 'views', 'placeholder',
            'in_stock', 'attributes')

class TileSerializerBulk(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Tile
        fields = ('id', 'feed', 'template', 'products', 'content', 'priority', 'clicks', 'views', 'placeholder',
            'in_stock', 'attributes')
        list_serializer_class = BulkListSerializer

class FeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = ('id', 'feed_algorithm', 'feed_ratio', 'store', 'is_finite', 'source_urls',
            'spider_name', 'created_at', 'updated_at')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'tiles', 'store', 'name', 'url', 'created_at', 'updated_at')
