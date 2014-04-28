from apps.scraper.scrapers.gap import GapProductScraper, GapCategoryScraper, STLScraper
from apps.scraper.scrapers.madewell import MadewellProductScraper, MadewellCategoryScraper, MadewellMultiProductScraper
from apps.scraper.scrapers.pinterest import PinterestPinScraper, PinterestAlbumScraper
from apps.scraper.scrapers.styldby import StyldByFilterScraper, StyldByPartnersScraper
from apps.scraper.scrapers.voyage_prive import VoyagePriveCategoryScraper


ALL_SCRAPERS = [
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
