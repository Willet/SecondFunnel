{# /* use by passing a 'product' into this template #}
{
    "id": "{{ product.id }}",
    {% if product.id %}
        "content-id": {{ product.id|escapejs }},  {# by default, anyway #}
        "db-id": {{ product.id|escapejs }},
    {% endif %}

    "description": "{{ product.description|escapejs }}",
    "name": "{{ product.name|escapejs }}",
    "title": "{{ product.name|escapejs }}",
    "price": "{{ product.price|escapejs }}",
    "template": "{{ product.template|default:'product' }}",
    "tags": {
        {% for key, value in product.tags.tags.items %}
            "{{ key }}": "{{ value }}"{% if not forloop.last %},{% endif %}
        {% endfor %}
    },
    {% if featured %}
        "stl-image": "{{ product.stl_image|escapejs }}",
        "featured-image": "{{ product.featured_image|escapejs }}",
    {% else %}
        "image": "{{ product.image }}",
    {% endif %}
    {% ifequal product.template "combobox" %}
        "lifestyle-image": "{{ product.lifestyle_image }}",
    {% endifequal %}
    "images": [
        {% for image in product.images %}
            {% if image %}
                "{{ image|escapejs }}"{% if not forloop.last %},{% endif %}
            {% endif %}
        {% endfor %}
    ],
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
        {# this is supposed to be an integer #}
        , "autoplay": {{ product.autoplay }}
    {% endif %}
}
{# */ #}