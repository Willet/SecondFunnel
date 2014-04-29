

def ALL_SCRAPERS():
    # why is this a function? it's a function because the imports need to be scoped.
    # but why is this function here? because ain't nobody got time to move it.
    from apps.scraper.scrapers.gap.gap_stl_scraper import STLScraper
    from apps.scraper.scrapers.gap.gap_product_scrapers import GapProductScraper, \
        GapCategoryScraper
    from apps.scraper.scrapers.madewell.madewell_product_scrapers import MadewellProductScraper, \
        MadewellCategoryScraper, MadewellMultiProductScraper
    from apps.scraper.scrapers.content.pinterest_scraper import PinterestPinScraper, \
        PinterestAlbumScraper
    from apps.scraper.scrapers.gap.styldby_scraper import StyldByFilterScraper, \
        StyldByPartnersScraper
    from apps.scraper.scrapers.voyage_prive.voyage_prive_scraper import VoyagePriveCategoryScraper

    return [
        GapProductScraper,
        GapCategoryScraper,
        MadewellProductScraper,
        MadewellCategoryScraper,
        MadewellMultiProductScraper,
        VoyagePriveCategoryScraper,
        PinterestPinScraper,
        PinterestAlbumScraper,
        StyldByFilterScraper,
        StyldByPartnersScraper,
        STLScraper,
    ]
