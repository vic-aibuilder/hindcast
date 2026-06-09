from __future__ import annotations

from pipeline.storage import (
    init_db,
    save_images,
    save_extraction,
    hash_brief,
    image_has_extraction,
)
from src.extractor import extract
from retrieval.consolidate import _consolidate_images

SEED_IMAGES_FASHION: list[dict] = [
    {
        "image_url": "https://static.dezeen.com/uploads/2026/05/issey-miyake-store-nomad_so-il_dezeen_hero1.jpg",
        "source_url": "https://www.dezeen.com/2026/05/08/issey-miyake-store-nomad-new-york-so-il/",
        "title": "Issey Miyake Nomad New York by SO-IL — hero",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2026/05/issey-miyake-store-nomad_so-il_dezeen_2364_col_6-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2026/05/08/issey-miyake-store-nomad-new-york-so-il/",
        "title": "Issey Miyake Nomad New York by SO-IL — interior 1",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2026/05/issey-miyake-store-nomad_so-il_dezeen_2364_col_1-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2026/05/08/issey-miyake-store-nomad-new-york-so-il/",
        "title": "Issey Miyake Nomad New York by SO-IL — interior 2",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2026/05/issey-miyake-store-nomad_so-il_dezeen_2364_col_2-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2026/05/08/issey-miyake-store-nomad-new-york-so-il/",
        "title": "Issey Miyake Nomad New York by SO-IL — interior 3",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2026/05/issey-miyake-store-nomad_so-il_dezeen_2364_col_3-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2026/05/08/issey-miyake-store-nomad-new-york-so-il/",
        "title": "Issey Miyake Nomad New York by SO-IL — interior 4",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2026/05/issey-miyake-store-nomad_so-il_dezeen_2364_col_5-1704x2556.jpg",
        "source_url": "https://www.dezeen.com/2026/05/08/issey-miyake-store-nomad-new-york-so-il/",
        "title": "Issey Miyake Nomad New York by SO-IL — interior 5",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2026/05/issey-miyake-store-nomad_so-il_dezeen_2364_col_4-1704x2556.jpg",
        "source_url": "https://www.dezeen.com/2026/05/08/issey-miyake-store-nomad-new-york-so-il/",
        "title": "Issey Miyake Nomad New York by SO-IL — interior 6",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc1ad16bd7f634b922d_68bee41dd2122e4b301f13be_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-03.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 1",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b923b_68bee41ae669aabf852a5348_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-04.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 2",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc0ad16bd7f634b921b_68bee41c03d16ae4f446706f_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-05.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 3",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc1ad16bd7f634b9224_68bee41c512862cbd46563c0_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-06.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 4",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b9238_68bee41adc95954ce2a6673b_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-07.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 5",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc1ad16bd7f634b9227_68bee4198df45a37554729a3_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-08.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 6",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc1ad16bd7f634b922a_68bee419aa429feb9496d2fa_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-09.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 7",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b9253_68bee418344d8d2453e08c50_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-10.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 8",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b924a_68bee41766e7dc3881aa497f_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-11.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 9",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b923e_68bee416f58fbf65107957a3_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-12.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 10",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b9241_68bee416852c4f722329cc5f_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-13.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 11",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b9250_68bee418e408a488636840f9_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-14.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 12",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://cdn.prod.website-files.com/5d70caf362d15d860bedae09/69c77dc2ad16bd7f634b9247_68bee4186a3724df4185e66a_thisispaper-acne-studios-greene-street-arquitectura-g-new-york-guide-16.webp",
        "source_url": "https://www.thisispaper.com/mag/acne-studios-greene-street-arquitectura-g",
        "title": "Acne Studios Greene Street New York — interior 14",
        "source": "thisispaper.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/01_e9752d8c-94a6-4011-86fa-be3c695fc820.jpg?v=1749227379&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 1",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/02_f82e0529-64a9-4ebe-9c84-dd6352a33ee9.jpg?v=1749227388&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 2",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/03_334b4732-64de-45ef-8cee-03081cff7cc3.jpg?v=1749227396&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 3",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/seandavidson_madhappy_nyc_8.jpg?v=1749227604&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 4",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/06_682da303-736b-42d9-a1c2-a85c19d20466.jpg?v=1749227429&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 5",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/07.jpg?v=1749227436&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 6",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/08.jpg?v=1749227443&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 7",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/seandavidson_madhappy_nyc_27.jpg?v=1749227604&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 8",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://www.madhappy.com/cdn/shop/files/09.jpg?v=1749227485&width=2400",
        "source_url": "https://www.madhappy.com/pages/stores/madhappy-new-york",
        "title": "Madhappy New York store — interior 9",
        "source": "madhappy.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/PkcVpKWyqcbExWiEnf4cyV-1600-80.jpeg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/john-lobb-700-madison-avenue-new-york",
        "title": "John Lobb 700 Madison Avenue New York — interior 1",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/oRUdHny8EKhfJg9B8nmmyV-1600-80.jpeg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/john-lobb-700-madison-avenue-new-york",
        "title": "John Lobb 700 Madison Avenue New York — interior 2",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/ck6sm8uCWjegpfpZhvf93W-1600-80.jpeg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/john-lobb-700-madison-avenue-new-york",
        "title": "John Lobb 700 Madison Avenue New York — interior 3",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/VtV6xbX9fjvDiprGF2pB3W-1600-80.jpeg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/john-lobb-700-madison-avenue-new-york",
        "title": "John Lobb 700 Madison Avenue New York — interior 4",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/01/road-to-awe_nyc-store_dan-brunn-architecture_dezeen_2364_col_10-1704x2272.jpg",
        "source_url": "https://www.dezeen.com/2023/01/08/road-to-awe-rta-nyc-soho-store-dan-brunn-architecture/",
        "title": "Road to Awe RTA NYC SoHo by Dan Brunn Architecture — interior 1",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/01/road-to-awe_nyc-store_dan-brunn-architecture_dezeen_2364_col_2-1704x2272.jpg",
        "source_url": "https://www.dezeen.com/2023/01/08/road-to-awe-rta-nyc-soho-store-dan-brunn-architecture/",
        "title": "Road to Awe RTA NYC SoHo by Dan Brunn Architecture — interior 2",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/01/road-to-awe_nyc-store_dan-brunn-architecture_dezeen_2364_col_19-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2023/01/08/road-to-awe-rta-nyc-soho-store-dan-brunn-architecture/",
        "title": "Road to Awe RTA NYC SoHo by Dan Brunn Architecture — interior 3",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/01/road-to-awe_nyc-store_dan-brunn-architecture_dezeen_2364_col_13-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2023/01/08/road-to-awe-rta-nyc-soho-store-dan-brunn-architecture/",
        "title": "Road to Awe RTA NYC SoHo by Dan Brunn Architecture — interior 4",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/01/road-to-awe_nyc-store_dan-brunn-architecture_dezeen_2364_col_4-1704x2272.jpg",
        "source_url": "https://www.dezeen.com/2023/01/08/road-to-awe-rta-nyc-soho-store-dan-brunn-architecture/",
        "title": "Road to Awe RTA NYC SoHo by Dan Brunn Architecture — interior 5",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/DR2T4EgewoBfTNqTfP2izW-1920-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/ulla-johnson-new-york-store-upper-east-side",
        "title": "Ulla Johnson Upper East Side New York — interior 1",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/QhtRfkaoKHQLXyaAR9722X-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/ulla-johnson-new-york-store-upper-east-side",
        "title": "Ulla Johnson Upper East Side New York — interior 2",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/XosxqatF2VfW5yHbqAwa2X-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/ulla-johnson-new-york-store-upper-east-side",
        "title": "Ulla Johnson Upper East Side New York — interior 3",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/ZP4CEu5T5igrfQGh9zTu9X-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/ulla-johnson-new-york-store-upper-east-side",
        "title": "Ulla Johnson Upper East Side New York — interior 4",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/XrNgLxKqiVRHEi9kCWNk6X-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/ulla-johnson-new-york-store-upper-east-side",
        "title": "Ulla Johnson Upper East Side New York — interior 5",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/qJBpjsmQd43UkCSG8BU27X-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/ulla-johnson-new-york-store-upper-east-side",
        "title": "Ulla Johnson Upper East Side New York — interior 6",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/6jswrv2E9NxnfJsA9xY97X-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/ulla-johnson-new-york-store-upper-east-side",
        "title": "Ulla Johnson Upper East Side New York — interior 7",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/bpm6tmjtjdrQmFrtUSXmwb-1200-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/extreme-cashmere-new-york-soho-store",
        "title": "Extreme Cashmere SoHo New York — interior 1",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/Wkn7L6KXMwhvSYoXj4emwb-1200-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/extreme-cashmere-new-york-soho-store",
        "title": "Extreme Cashmere SoHo New York — interior 2",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/mAhLwMccmQRpV6e5Wk2rwb-801-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/extreme-cashmere-new-york-soho-store",
        "title": "Extreme Cashmere SoHo New York — interior 3",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/FrYzmpwXjxUocBngg3hfwb-801-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/extreme-cashmere-new-york-soho-store",
        "title": "Extreme Cashmere SoHo New York — interior 4",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/Bq5rnFybfUMmYAWuJGWNeN-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/house-of-dior-new-york-store",
        "title": "House of Dior New York — interior 1",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/yGqqht75g42WAgDSoQhgvN-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/house-of-dior-new-york-store",
        "title": "House of Dior New York — interior 2",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/qYcuS29ckBqccGdoH5hwYM-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/house-of-dior-new-york-store",
        "title": "House of Dior New York — interior 3",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/ab6p9UUuJTbWNEkxQLQfy5-1920-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/stone-island-new-york-store",
        "title": "Stone Island New York store — interior 1",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/xPLXg443xnGp4abUYAj8x5-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/stone-island-new-york-store",
        "title": "Stone Island New York store — interior 2",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/Q5XJcVCKRAZTjeKrYsFqA6-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/stone-island-new-york-store",
        "title": "Stone Island New York store — interior 3",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/TSEo5UmZFX6a4UWbKvVYz5-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/stone-island-new-york-store",
        "title": "Stone Island New York store — interior 4",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/D6obwsiACvPxmpk7TLLdz5-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/stone-island-new-york-store",
        "title": "Stone Island New York store — interior 5",
        "source": "wallpaper.com",
    },
    {
        "image_url": "https://cdn.mos.cms.futurecdn.net/5PPgAvKBbzNJqihUwvh5L6-1600-80.jpg.webp",
        "source_url": "https://www.wallpaper.com/fashion-beauty/stone-island-new-york-store",
        "title": "Stone Island New York store — interior 6",
        "source": "wallpaper.com",
    },
]

SEED_IMAGES_SNEAKER: list[dict] = [
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_7-1704x2130.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 1",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_9-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 2",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_15-1704x2130.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 3",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_20-1704x2130.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 4",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_17-1704x2130.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 5",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_16.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 6",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_13-scaled.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 7",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_11.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 8",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_19-scaled.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 9",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2024/02/kith-women-soho_dezeen_2364_col_21-scaled.jpg",
        "source_url": "https://www.dezeen.com/2024/02/17/kith-women-flagship-soho-new-york/",
        "title": "Kith Women flagship SoHo New York — interior 10",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/03/kith-williamsburg-_dezeen_2364_hero.jpg",
        "source_url": "https://www.dezeen.com/2023/03/24/kith-creates-industrial-ambiance-for-its-williamsburg-store/",
        "title": "Kith Williamsburg Brooklyn — hero",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/03/kith-williamsburg-_dezeen_2364_col_8-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2023/03/24/kith-creates-industrial-ambiance-for-its-williamsburg-store/",
        "title": "Kith Williamsburg Brooklyn — interior 1",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/03/kith-williamsburg-_dezeen_2364_col_3-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2023/03/24/kith-creates-industrial-ambiance-for-its-williamsburg-store/",
        "title": "Kith Williamsburg Brooklyn — interior 2",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/03/kith-williamsburg-_dezeen_2364_col_6-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2023/03/24/kith-creates-industrial-ambiance-for-its-williamsburg-store/",
        "title": "Kith Williamsburg Brooklyn — interior 3",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/03/kith-williamsburg-_dezeen_2364_col_5-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2023/03/24/kith-creates-industrial-ambiance-for-its-williamsburg-store/",
        "title": "Kith Williamsburg Brooklyn — interior 4",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/03/kith-williamsburg-_dezeen_2364_col_7-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2023/03/24/kith-creates-industrial-ambiance-for-its-williamsburg-store/",
        "title": "Kith Williamsburg Brooklyn — interior 5",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2023/03/kith-williamsburg-_dezeen_2364_col_9-1704x959.jpg",
        "source_url": "https://www.dezeen.com/2023/03/24/kith-creates-industrial-ambiance-for-its-williamsburg-store/",
        "title": "Kith Williamsburg Brooklyn — interior 6",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2026%2F05%2F06%2F87A5143-scaled.jpg?w=3500&format=jpg&q=98&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2026/5/colbo-nyc-interview-feature",
        "title": "Colbo NYC sneaker boutique — interior 1",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2026%2F05%2F06%2F87A5077-scaled.jpg?w=3500&format=jpg&q=98&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2026/5/colbo-nyc-interview-feature",
        "title": "Colbo NYC sneaker boutique — interior 2",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2026%2F05%2F06%2F87A5153-scaled.jpg?w=3500&format=jpg&q=98&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2026/5/colbo-nyc-interview-feature",
        "title": "Colbo NYC sneaker boutique — interior 3",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2026%2F05%2F06%2F87A5119-scaled.jpg?w=3500&format=jpg&q=98&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2026/5/colbo-nyc-interview-feature",
        "title": "Colbo NYC sneaker boutique — interior 4",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2026%2F05%2F06%2F87A5123-scaled.jpg?w=3500&format=jpg&q=98&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2026/5/colbo-nyc-interview-feature",
        "title": "Colbo NYC sneaker boutique — interior 5",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2026%2F05%2F06%2F87A5081-scaled.jpg?w=3500&format=jpg&q=98&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2026/5/colbo-nyc-interview-feature",
        "title": "Colbo NYC sneaker boutique — interior 6",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1560361318218-HT8SSOG8Y6TXMZP5VL3E/_72A0138.jpg?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 1",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1560361528513-BLO5JFBPD4BBZ5I21468/_72A0244.jpg?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 2",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1560361027995-RRWKXM5GO8XGGC54IGY9/472A7202.JPG?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 3",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1560361630146-EFWK24F70H5IKJVGRFM0/image-asset.jpeg?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 4",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1566500276705-WM647BKG1RCVX6TVHHR2/472A7256.JPG?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 5",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1560361963467-GA1Z5APQ94XXS2LXCAKH/_72A9968.jpg?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 6",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1566501000236-EHGT757R4EQZQ8CQ80WQ/472A7445.jpg?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 7",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://images.squarespace-cdn.com/content/v1/5281199de4b042587830c5e5/1560362111299-DXENF3J18A37BDUKMIGB/_72A0064.jpg?format=2500w",
        "source_url": "https://www.sladearch.com/flight-club-ny",
        "title": "Flight Club New York by Slade Architecture — interior 8",
        "source": "sladearch.com",
    },
    {
        "image_url": "https://wwd.com/wp-content/uploads/2025/09/250911-New-Balance-Flatiron-Opening-Rush-26.jpg?w=1000&h=563&crop=1&resize=1000%2C563",
        "source_url": "https://wwd.com/footwear-news/shoe-industry-news/new-balance-flatiron-nyc-flagship-store-remodeled-1238145507/",
        "title": "New Balance Flatiron NYC flagship remodel — interior 1",
        "source": "wwd.com",
    },
    {
        "image_url": "https://wwd.com/wp-content/uploads/2025/09/250911-New-Balance-Flatiron-Opening-Rush-27.jpg",
        "source_url": "https://wwd.com/footwear-news/shoe-industry-news/new-balance-flatiron-nyc-flagship-store-remodeled-1238145507/",
        "title": "New Balance Flatiron NYC flagship remodel — interior 2",
        "source": "wwd.com",
    },
    {
        "image_url": "https://wwd.com/wp-content/uploads/2025/09/250911-New-Balance-Flatiron-Opening-Rush-28.jpg",
        "source_url": "https://wwd.com/footwear-news/shoe-industry-news/new-balance-flatiron-nyc-flagship-store-remodeled-1238145507/",
        "title": "New Balance Flatiron NYC flagship remodel — interior 3",
        "source": "wwd.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F02%2F12%2Fstussy-new-york-chapter-flagship-store-reopening-info-002.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/2/stussy-new-york-chapter-flagship-store-reopening-info",
        "title": "Stussy New York Chapter flagship reopening — interior 1",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F02%2F12%2Fstussy-new-york-chapter-flagship-store-reopening-info-003.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/2/stussy-new-york-chapter-flagship-store-reopening-info",
        "title": "Stussy New York Chapter flagship reopening — interior 2",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F02%2F12%2Fstussy-new-york-chapter-flagship-store-reopening-info-004.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/2/stussy-new-york-chapter-flagship-store-reopening-info",
        "title": "Stussy New York Chapter flagship reopening — interior 3",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F02%2F12%2Fstussy-new-york-chapter-flagship-store-reopening-info-005.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/2/stussy-new-york-chapter-flagship-store-reopening-info",
        "title": "Stussy New York Chapter flagship reopening — interior 4",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F02%2F12%2Fstussy-new-york-chapter-flagship-store-reopening-info-010.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/2/stussy-new-york-chapter-flagship-store-reopening-info",
        "title": "Stussy New York Chapter flagship reopening — interior 5",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F02%2F12%2Fstussy-new-york-chapter-flagship-store-reopening-info-012.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/2/stussy-new-york-chapter-flagship-store-reopening-info",
        "title": "Stussy New York Chapter flagship reopening — interior 6",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F02%2F12%2Fstussy-new-york-chapter-flagship-store-reopening-info-007.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/2/stussy-new-york-chapter-flagship-store-reopening-info",
        "title": "Stussy New York Chapter flagship reopening — interior 7",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F05%2F26%2Fbrain-dead-nyc-store-opening-info-002.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/5/brain-dead-new-york-city-202-elizabeth-street-store-opening-info",
        "title": "Brain Dead NYC Elizabeth Street store opening — interior 1",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F05%2F26%2Fbrain-dead-nyc-store-opening-info-004.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/5/brain-dead-new-york-city-202-elizabeth-street-store-opening-info",
        "title": "Brain Dead NYC Elizabeth Street store opening — interior 2",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F05%2F26%2Fbrain-dead-nyc-store-opening-info-005.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/5/brain-dead-new-york-city-202-elizabeth-street-store-opening-info",
        "title": "Brain Dead NYC Elizabeth Street store opening — interior 3",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F05%2F26%2Fbrain-dead-nyc-store-opening-info-006.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/5/brain-dead-new-york-city-202-elizabeth-street-store-opening-info",
        "title": "Brain Dead NYC Elizabeth Street store opening — interior 4",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://image-cdn.hypb.st/https%3A%2F%2Fhypebeast.com%2Fimage%2F2025%2F05%2F26%2Fbrain-dead-nyc-store-opening-info-008.jpg?q=90&w=1400&cbr=1&fit=max",
        "source_url": "https://hypebeast.com/2025/5/brain-dead-new-york-city-202-elizabeth-street-store-opening-info",
        "title": "Brain Dead NYC Elizabeth Street store opening — interior 5",
        "source": "hypebeast.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore_04-1200x800.jpeg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 1",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore_03.jpeg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 2",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore_06.jpeg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 3",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore_02-e1683754828216.jpeg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 4",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore-nyc-3.jpg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 5",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore-nyc-5.jpg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 6",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore-nyc-11.jpg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 7",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore-nyc-7.jpg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 8",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://sixtysixmag.com/wp-content/uploads/aime-leon-dore-nyc-10.jpg",
        "source_url": "https://sixtysixmag.com/aime-leon-dore-nyc/",
        "title": "Aimé Leon Dore NYC — interior 9",
        "source": "sixtysixmag.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2018/05/supreme-brooklyn-store-neil-logan-architect-interiors-retail-new-york-city-usa_dezeen_2364_hero.jpg",
        "source_url": "https://www.dezeen.com/2018/05/26/supreme-store-brooklyn-features-elevated-skate-bowl-neil-logan-architect/",
        "title": "Supreme Brooklyn by Neil Logan Architect — hero",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2018/05/supreme-brooklyn-store-neil-logan-architect-interiors-retail-new-york-city-usa_dezeen_2364_col_1-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2018/05/26/supreme-store-brooklyn-features-elevated-skate-bowl-neil-logan-architect/",
        "title": "Supreme Brooklyn by Neil Logan Architect — interior 1",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2018/05/supreme-brooklyn-store-neil-logan-architect-interiors-retail-new-york-city-usa_dezeen_2364_col_9-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2018/05/26/supreme-store-brooklyn-features-elevated-skate-bowl-neil-logan-architect/",
        "title": "Supreme Brooklyn by Neil Logan Architect — interior 2",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2018/05/supreme-brooklyn-store-neil-logan-architect-interiors-retail-new-york-city-usa_dezeen_2364_col_3-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2018/05/26/supreme-store-brooklyn-features-elevated-skate-bowl-neil-logan-architect/",
        "title": "Supreme Brooklyn by Neil Logan Architect — interior 3",
        "source": "dezeen.com",
    },
    {
        "image_url": "https://static.dezeen.com/uploads/2018/05/supreme-brooklyn-store-neil-logan-architect-interiors-retail-new-york-city-usa_dezeen_2364_col_14-1704x1136.jpg",
        "source_url": "https://www.dezeen.com/2018/05/26/supreme-store-brooklyn-features-elevated-skate-bowl-neil-logan-architect/",
        "title": "Supreme Brooklyn by Neil Logan Architect — interior 4",
        "source": "dezeen.com",
    },
]


SEED_BRIEF = "__seed_corpus__"

# Per-source cap for the curated seed corpus. Looser than live retrieval's
# MAX_IMAGES_PER_SOURCE (6): these images are hand-picked, so there is no
# listicle-flood risk and a well-documented store can keep more shots.
SEED_MAX_IMAGES_PER_SOURCE = 8


def load_slice(images: list[dict], sub_slice: str) -> None:
    if not images:
        print(f"  No seed images defined for {sub_slice} — skipping.")
        return

    # Same dedupe + per-source cap + interleave as live retrieval, but with the
    # looser seed cap (see SEED_MAX_IMAGES_PER_SOURCE).
    images = _consolidate_images(images, max_per_source=SEED_MAX_IMAGES_PER_SOURCE)

    print(f"\nLoading seed corpus: {sub_slice}")
    print(f"  {len(images)} images to process...")

    brief_hash = hash_brief(SEED_BRIEF, sub_slice)
    saved_ids = save_images(images, sub_slice, brief_hash)
    print(f"  Saved {len(saved_ids)} new images to database.")

    # Look up IDs for images already in the database
    from pipeline.storage import get_connection

    conn = get_connection()
    for img in images:
        if img.get("id"):
            continue
        row = conn.execute(
            "SELECT id FROM images WHERE image_url = ?",
            (img.get("image_url", ""),),
        ).fetchone()
        if row:
            img["id"] = row["id"]
    conn.close()

    extracted = 0
    skipped = 0
    failed = 0

    for img in images:
        image_id = img.get("id")
        image_url = img.get("image_url", "")

        if not image_id or not image_url:
            continue

        if image_has_extraction(image_id):
            skipped += 1
            continue

        try:
            schema = extract(image_url)
            if schema:
                save_extraction(image_id, schema, sub_slice)
                extracted += 1
                print(f"  [{extracted}] {img.get('title', '')[:50]}")
        except Exception as e:
            failed += 1
            print(f"  failed: {image_url[:60]} ({e})")
            continue

    print(f"  Done — {extracted} extracted, {skipped} skipped, {failed} failed.")


def load_all() -> None:
    init_db()
    print("Loading Hindcast seed corpus...")
    load_slice(SEED_IMAGES_SNEAKER, "sneaker_streetwear")
    load_slice(SEED_IMAGES_FASHION, "contemporary_fashion")

    from pipeline.storage import corpus_stats

    stats = corpus_stats()
    print("\nSeed corpus complete.")
    print(f"  Total images: {stats['total_images']}")
    print(f"  By slice: {stats['by_slice']}")
    print(f"  Extractions: {stats['total_extractions']}")


if __name__ == "__main__":
    load_all()
