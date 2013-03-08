{# use by passing a list of 'products' into this template #}
[
    {% for product in products %}
    {% include 'pinpoint/snippets/product_object.js' with product=product featured=False only %}
    {% if not forloop.last %},{% endif %}
    {% endfor %}
]