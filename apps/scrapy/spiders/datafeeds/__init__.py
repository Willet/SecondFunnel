# http://doc.scrapy.org/en/latest/topics/item-pipeline.html#activating-an-item-pipeline-component
ITEM_PIPELINES = {
    # 1's - Validation
    'apps.scrapy.pipelines.ForeignKeyPipeline': 1,
    'apps.scrapy.pipelines.ValidationPipeline': 3,
    'apps.scrapy.pipelines.DuplicatesPipeline': 5,
    # 10 - Sanitize and generate attributes
    'apps.scrapy.pipelines.PricePipeline': 11,
    'apps.scrapy.pipelines.ContentImagePipeline': 12,
    # 40 - Persistence-related
    'apps.scrapy.pipelines.ItemPersistencePipeline': 40,
    'apps.scrapy.pipelines.AssociateWithProductsPipeline': 41,
    'apps.scrapy.pipelines.TagPipeline': 42,
    'apps.scrapy.pipelines.ProductImagePipeline': 47,
    # 50 - 
    'apps.scrapy.pipelines.TileCreationPipeline': 50,
    'apps.scrapy.pipelines.SimilarProductsPipeline': 52,
    # 90 - Scrape job control
    'apps.scrapy.pipelines.PageUpdatePipeline': 99,
}
