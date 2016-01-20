from rest_framework import serializers
from django.contrib.auth.models import User

from apps.assets.models import Store, Product, Content, Image, Gif, ProductImage, Video, Page, Tile

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('staff', 'name', 'description', 'slug', 'display_out_of_stock', 'default_theme',
            'default_page', 'public_base_url')

class ProductSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Product
        fields = ('store', 'name', 'description', 'details', 'url', 'sku', 'price', 'sale_price', 
            'currency', 'default_image', 'last_scraped_at', 'in_stock', 'attributes', 'similar_products')

class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ('store', 'url', 'source', 'source_url', 'author', 'tagged_products', 
            'attributes', 'status')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('name', 'description', 'original_url', 'file_type', 'file_checksum', 'width', 'height',
            'dominant_color','store', 'url', 'source', 'source_url', 'author', 'tagged_products', 'attributes',
            'status')

class GifSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gif
        fields = ('gif_url', 'name', 'description', 'original_url', 'file_type', 'file_checksum', 'width', 
            'height', 'dominant_color','store', 'url', 'source', 'source_url', 'author', 'tagged_products',
            'attributes', 'status')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('product', 'url', 'original_url', 'file_type', 'file_checksum', 'width', 'height', 
            'dominant_color', 'image_sizes', 'attributes')

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('name', 'caption', 'username', 'description', 'player', 'file_type', 'file_checksum', 
            'original_id', 'store', 'url', 'source', 'source_url', 'author', 'tagged_products', 
            'attributes', 'status')

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('store', 'name', 'theme', 'theme_settings', 'dashboard_settings', 'campaign', 
            'description', 'url_slug', 'legal_copy', 'last_published_at', 'feed')

class TileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tile
        fields = ('feed', 'template', 'products', 'priority', 'clicks', 'views', 'placeholder',
            'in_stock', 'attributes')
        