{# use by passing a 'product' into this template #}
{
    "product-id": "{{ product.id }}",
    "id": "{{ product.id }}",
    "lifestyle_image": "{{ product.lifestyle_image|escapejs }}",
    "lifestyle-image": "{{ product.lifestyle_image|escapejs }}",
    "featured_image": "{{ product.featured_image|escapejs }}",
    "description": "{{ product.description|escapejs }}",
    "name": "{{ product.name|escapejs }}",
    "title": "{{ product.name|escapejs }}",
    "price": "{{ product.price|escapejs }}",
    "template": "{{ product.template|default:'product'|escapejs }}",
    "images": [
    {% for image in product.images %}
        {% if image %}
        "{{ image|escapejs }}"{% if not forloop.last %},{% endif %}
        {% endif %}
    {% endfor %}
    ],
    "image": "{{ product.images.0|escapejs }}",
    "url": "{{ product.url|escapejs }}"
}