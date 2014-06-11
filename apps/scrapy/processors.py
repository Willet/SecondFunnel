def cleanup_price(price, loader_context):
    price = price.strip()

    # TODO: Maybe have default currency options in options?
    # TODO: Couldn't `locale.atof` handle this?
    currency_info = loader_context.get('currency_info', {})
    symbol = currency_info.get('symbol', '$')
    group = currency_info.get('group', ',')
    #position_at_end = currency_info.get('position-at-end')

    price = price.strip(symbol)
    price = ''.join(price.split(group))
    price = float(price)

    # Our Product model uses a narrow regex...
    # So, forget all this fanciness until that is changed.

    # if position_at_end:
    #     template = u'{price}{symbol}'
    # else:
    #     template = u'{symbol}{price}'

    # item['price'] = template.format(price=item['price'], symbol=symbol)
    price = u'{symbol}{price:0.2f}'.format(
        price=price, symbol=symbol
    )
    return price
