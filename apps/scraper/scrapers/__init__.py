

def ALL_SCRAPERS():
    # why is this a function? it's a function because the imports need to be scoped.
    # but why is this function here? because ain't nobody got time to move it.
    from apps.scraper.scrapers.gap import GapProductScraper, \
        GapCategoryScraper, STLScraper
    from apps.scraper.scrapers.madewell import MadewellProductScraper, \
        MadewellCategoryScraper, MadewellMultiProductScraper
    from apps.scraper.scrapers.pinterest import PinterestPinScraper, \
        PinterestAlbumScraper
    from apps.scraper.scrapers.styldby import StyldByFilterScraper, \
        StyldByPartnersScraper
    from apps.scraper.scrapers.voyage_prive import VoyagePriveCategoryScraper

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
