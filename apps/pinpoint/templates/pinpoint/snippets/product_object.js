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

    {# one thing led to another, and we are using this as some generic object now #}
    {% if product.provider %}
        , "provider": "{{ product.provider|default:'youtube' }}"
    {% endif %}
    {% if product.width %}
        , "width": "{{ product.width }}"
    {% endif %}
    {% if product.width %}
        , "height": "{{ product.height }}"
    {% endif %}
    {% if product.autoplay %}
        {# this is supposed to be an integer }
        , "autoplay": {{ product.autoplay }}
    {% endif %}
}