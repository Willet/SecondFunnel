# temporary, used for data migration

import re
price_pattern = re.compile('\d+.\d{0,2}')

for prod in Product.objects.order_by('id'):
    price = price_pattern.findall(prod.price)[0]
    prod.price1 = float(price)
    sale_price = prod.attributes.get('sale_price')
    if sale_price:
        prod.sale_price = float(price_pattern.findall(sale_price)[0])
    print prod.id, ':', prod.price1, prod.sale_price
    if prod.store.name != "Columbia":
        prod.save()
