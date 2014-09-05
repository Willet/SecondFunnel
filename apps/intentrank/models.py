class TileList(list):
    @property
    def ids(self):
        tile_ids = []
        for x in self:
            if type(x) == int:
                tile_ids.append(x)
            else:
                tile_ids.append(getattr(x, 'id', 0))
        return tile_ids

    @property
    def products(self):
        return self.__class__([x for x in self if getattr(
            x, 'template', 'product') == 'product'])

    @property
    def products_count(self):
        return len(self.products)

    @property
    def contents(self):
        return self.__class__([x for x in self if getattr(
            x, 'template', 'product') != 'product'])

    @property
    def contents_count(self):
        return len(self.contents)
