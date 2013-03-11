{# use by passing a 'product' into this template #}
{
    "id": "{{ product.id }}",
    "description": "{{ product.description|escapejs }}",
    "name": "{{ product.name|escapejs }}",
    "title": "{{ product.name|escapejs }}",
    "price": "{{ product.price|escapejs }}",
    "template": "{{ product.template|default:'product' }}",
    {% if featured %}
    "stl-image": "{{ product.stl_image|escapejs }}",
    "featured-image": "{{ product.featured_image|escapejs }}",
    {% else %}
    "image": "{{ product.image }}",
    {% endif %}
    "images": [
    {% for image in product.images %}
        {% if image %}
        "{{ image|escapejs }}"{% if not forloop.last %},{% endif %}
        {% endif %}
    {% endfor %}
    ],
    "url": "{{ product.url|escapejs }}"
}