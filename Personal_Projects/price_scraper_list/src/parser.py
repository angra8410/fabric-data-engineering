import re
import unicodedata
from typing import Optional

from pydantic import BaseModel


class ParsedProduct(BaseModel):
    product_name: str
    price_current: float
    price_regular: Optional[float] = None
    discount_pct: Optional[float] = None
    unit_price_value: Optional[float] = None
    unit_measure: Optional[str] = None
    package_weight: Optional[str] = None
    brand: str
    pet_type: str
    is_medical: bool
    in_stock: bool = True


class ProductParser:
    PRICE_PATTERN = re.compile(r"\$\s*([\d\.,]+)")
    DISCOUNT_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
    UNIT_PRICE_PATTERN = re.compile(r"\(\s*\$?\s*([\d\.,]+)\s*/\s*([a-zA-Z]+)\s*\)")
    WEIGHT_PATTERN = re.compile(
        r"(\d+(?:[.,]\d+)?\s*(?:kg|kilos?|g|gr|grs|gramos?|lb|lbs|libras?|ml|l|litros?|oz))\b",
        re.IGNORECASE,
    )
    OUT_OF_STOCK_WORDS = ("agotado", "no disponible", "sin existencias", "sin stock")
    UI_NOISE = {"agregar", "0", "+", "-", "ver más"}

    MEDICAL_KEYWORDS = [
        "prescription", "veterinary", "veterinaria", "veterinario", "medicado", "vet life", "vetlife",
        "i/d", "k/d", "c/d", "u/d", "z/d", "w/d", "j/d", "s/d", "r/d", "l/d", "t/d", "y/d",
        "hypoallergenic", "hipoalergenico", "hipoalergénico", "renal", "urinary", "urinario",
        "gastrointestinal", "hepatic", "hepatico", "hepático", "hepatocare", "cardiac",
        "obesity", "satiety", "recovery", "dermatology", "derm",
        "anallergenic", "mobility", "metabolic",
    ]

    BRANDS = {
        "Hill's": ["hills", "hill's", "hill´s", "science diet", "prescription diet"],
        "Royal Canin": ["royal canin"],
        "Purina Pro Plan": ["pro plan", "proplan", "purina pro plan"],
        "Purina One": ["purina one"],
        "Farmina Vet Life": ["vet life", "vetlife", "farmina"],
        "Tierragro": ["tierragro"],
        "Equilibrio": ["equilibrio"],
        "Diamond": ["diamond"],
        "Taste of the Wild": ["taste of the wild"],
        "Chunky": ["chunky"],
        "Pedigree": ["pedigree"],
        "Whiskas": ["whiskas"],
        "Dog Chow": ["dog chow"],
        "Cat Chow": ["cat chow"],
    }

    DOG_PATTERN = re.compile(
        r"\b(perr[oa]s?|canin[oae]s?|cachorr[oa]s?|puppy|dogs?|small bites|large breed|small paws)\b"
    )
    CAT_PATTERN = re.compile(r"\b(gat[oa]s?|gatitos?|felin[oae]s?|kittens?|cats?)\b")

    # ------------------------------------------------------------------ prices
    @classmethod
    def clean_cop_price(cls, raw: Optional[str]) -> Optional[float]:
        """
        Parses Colombian peso formatting into a float. Dots are thousand
        separators, comma is the decimal separator:
            '115.750,00' -> 115750.0   '264.505' -> 264505.0
        Returns None for anything that cannot be parsed.
        """
        if not raw:
            return None
        cleaned = re.sub(r"[^\d.,]", "", raw)
        if not cleaned:
            return None
        if "," in cleaned:
            integer_part, _, decimal_part = cleaned.rpartition(",")
            integer_part = integer_part.replace(".", "").replace(",", "")
            if not decimal_part.isdigit() or len(decimal_part) > 2:
                # comma used as thousands separator, e.g. '115,750'
                integer_part, decimal_part = integer_part + decimal_part, "0"
            cleaned = f"{integer_part or '0'}.{decimal_part}"
        else:
            cleaned = cleaned.replace(".", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def parse_price_text(cls, text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        m = cls.PRICE_PATTERN.search(text.replace("\xa0", " "))
        value = cls.clean_cop_price(m.group(1) if m else text)
        return value if value and value > 0 else None

    @classmethod
    def clean_unit_price(cls, raw: Optional[str]) -> Optional[float]:
        """Parses unit prices like '57.88' or '57,88' -> 57.88"""
        if not raw:
            return None
        cleaned = raw.strip().replace("\xa0", "").replace("$", "").strip().replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def parse_unit_price(cls, text: Optional[str]) -> tuple[Optional[float], Optional[str]]:
        if not text:
            return None, None
        m = cls.UNIT_PRICE_PATTERN.search(text)
        if not m:
            return None, None
        return cls.clean_unit_price(m.group(1)), m.group(2).lower()

    @classmethod
    def parse_discount(cls, text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        m = cls.DISCOUNT_PATTERN.search(text)
        return float(m.group(1).replace(",", ".")) if m else None

    # -------------------------------------------------------------- classifiers
    @classmethod
    def detect_brand(cls, text: str) -> str:
        low = text.lower()
        for brand, patterns in cls.BRANDS.items():
            if any(p in low for p in patterns):
                return brand
        return "Other / Store Brand"

    @classmethod
    def detect_pet_type(cls, text: str) -> str:
        low = text.lower()
        has_dog = bool(cls.DOG_PATTERN.search(low))
        has_cat = bool(cls.CAT_PATTERN.search(low))
        if has_dog and not has_cat:
            return "Dog"
        if has_cat and not has_dog:
            return "Cat"
        if has_dog and has_cat:
            return "Dog & Cat"
        return "Unknown / General"

    @classmethod
    def detect_medical(cls, text: str) -> bool:
        low = text.lower()
        return any(k in low for k in cls.MEDICAL_KEYWORDS)

    @classmethod
    def extract_weight(cls, text: str) -> Optional[str]:
        match = cls.WEIGHT_PATTERN.search(text)
        return match.group(1).strip() if match else None

    # ------------------------------------------------------------ match key
    # Words that stores add or drop freely without changing the product.
    KEY_STOPWORDS = {
        "alimento", "alimentos", "comida", "concentrado", "concentrados", "croquetas",
        "para", "de", "del", "la", "el", "los", "las", "en", "con", "y", "x", "por",
        "un", "una", "sabor", "receta", "bolsa", "bulto", "presentacion", "ref",
    }
    # Spanish/English variants collapsed to one token.
    KEY_SYNONYMS = {
        "hill's": "hills", "hill´s": "hills", "hill": "hills",
        "perros": "perro", "perra": "perro", "canino": "perro", "caninos": "perro", "canine": "perro",
        "dog": "perro", "dogs": "perro",
        "gatos": "gato", "felino": "gato", "felinos": "gato", "feline": "gato", "cat": "gato", "cats": "gato",
        "adultos": "adulto", "adult": "adulto", "adults": "adulto",
        "cachorros": "cachorro", "puppy": "cachorro", "puppies": "cachorro",
        "gatitos": "gatito", "kitten": "gatito", "kittens": "gatito",
        "humeda": "humedo", "wet": "humedo", "seca": "seco", "dry": "seco",
        "pequena": "pequeno", "pequenas": "pequeno", "pequenos": "pequeno", "small": "pequeno",
        "grande": "grande", "grandes": "grande", "large": "grande",
        "mediano": "mediano", "medianos": "mediano", "medium": "mediano",
        "raza": "raza", "razas": "raza", "breed": "raza",
        "pollo": "pollo", "chicken": "pollo",
        "veterinaria": "veterinary", "veterinario": "veterinary", "veterinarios": "veterinary",
        "dieta": "diet", "dietas": "diet", "diets": "diet",
    }
    KEY_WEIGHT_PATTERN = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:kg|kgs|kl|kilos?|g|gr|grs|gramos?|lb|lbs|libras?|ml|l|litros?|oz)\b"
    )

    @classmethod
    def match_key(cls, name: str) -> str:
        """
        Order-insensitive normalized name used to recognise the same product
        across stores that word it differently, e.g.
        "Hill's Comida Perro Adulto Small Bites 2 Kg" and
        "Alimento Hills Small Bites para Perros Adultos" -> same key.
        Package size is NOT part of the key (views add pack_size from the
        unit price, which is more reliable than the size written in names).
        """
        return " ".join(sorted(set(cls.key_tokens(name))))

    # Shorthand used in store inventories (not applied to stored product keys).
    INVENTORY_ABBREVIATIONS = [
        (r"^\(\w+\)\s*", ""),                       # "(VE) INABA ..." -> "INABA ..."
        (r"\bvet nat\b", "vet life natural"),
        (r"\bvete diets\b", "veterinary diets"),
        (r"\bvet diets\b", "veterinary diets"),
        (r"\bcalabza\b", "calabaza"),
        (r"\bfrango\b", "pollo"),                   # Portuguese labels
        (r"\bsuino\b", "cerdo"),
        (r"\bfel\b", "felino"),
    ]

    @classmethod
    def key_tokens(cls, name: str, inventory: bool = False) -> list[str]:
        """Normalized tokens in their original order (first one is usually the brand)."""
        text = unicodedata.normalize("NFKD", (name or "").lower())
        text = "".join(c for c in text if not unicodedata.combining(c))
        if inventory:
            for pattern, repl in cls.INVENTORY_ABBREVIATIONS:
                text = re.sub(pattern, repl, text)
        text = text.replace("hill's", "hills").replace("hill´s", "hills").replace("hill`s", "hills")
        text = cls.KEY_WEIGHT_PATTERN.sub(" ", text)
        text = re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", text)  # 2.000.000 UI -> 2000000
        text = text.replace("proplan", "pro plan").replace("vetlife", "vet life")
        text = re.sub(r"\b([a-z])/([a-z])\b", r"\1_\2", text)  # keep i/d, k/d ... as one token
        text = re.sub(r"[^a-z0-9_+ ]", " ", text)
        tokens: list[str] = []
        for tok in text.split():
            tok = cls.KEY_SYNONYMS.get(tok, tok).replace("_", "/")
            if tok not in cls.KEY_STOPWORDS and tok not in tokens:
                tokens.append(tok)
        return tokens

    SIZE_PATTERN = re.compile(
        r"(\d+(?:[.,]\d+)?)\s*(kg|kgs|kl|k|kilos?|g|gr|grs|gramos?|lb|lbs|libras?|ml|l|lt|litros?)\b",
        re.IGNORECASE,
    )
    SIZE_FACTORS = {"kg": 1000, "kgs": 1000, "kl": 1000, "k": 1000, "kilo": 1000, "kilos": 1000,
                    "g": 1, "gr": 1, "grs": 1, "gramo": 1, "gramos": 1,
                    "lb": 453.6, "lbs": 453.6, "libra": 453.6, "libras": 453.6,
                    "ml": 1, "l": 1000, "lt": 1000, "litro": 1000, "litros": 1000}

    @classmethod
    def size_in_base_units(cls, name: str) -> Optional[float]:
        """'ARENA MAIZ CAT 10 KG' -> 10000.0 (grams, or ml for liquids); None if absent."""
        m = cls.SIZE_PATTERN.search(name or "")
        if not m:
            return None
        return float(m.group(1).replace(",", ".")) * cls.SIZE_FACTORS[m.group(2).lower()]

    @classmethod
    def is_relevant(cls, query: str, product_name: str) -> bool:
        """
        Rappi fuzzy-matches every query (even nonsense returns products), so a
        result is kept only if it shares at least one normalized word with the
        query: 'vet life perro medicado' keeps any dog product but drops e.g.
        'Nobivac Kc (Tos Perreras)'. Store-name queries like 'tierragro perro'
        still work through the pet word.
        """
        def expand(key: str) -> set:
            tokens = set(key.split())
            # life-stage words also count as the species for relevance
            if "cachorro" in tokens:
                tokens.add("perro")
            if "gatito" in tokens:
                tokens.add("gato")
            return tokens
        return bool(expand(cls.match_key(query)) & expand(cls.match_key(product_name)))

    # ----------------------------------------------------------------- builders
    @classmethod
    def _build(
        cls,
        name: str,
        price_current: float,
        price_regular: Optional[float],
        discount_pct: Optional[float],
        unit_price: Optional[float],
        unit_measure: Optional[str],
        in_stock: bool,
    ) -> ParsedProduct:
        if price_regular is not None and price_regular <= price_current:
            price_regular = None
        if discount_pct is None and price_regular:
            discount_pct = round((1 - price_current / price_regular) * 100, 1)
        return ParsedProduct(
            product_name=name,
            price_current=price_current,
            price_regular=price_regular,
            discount_pct=discount_pct,
            unit_price_value=unit_price,
            unit_measure=unit_measure,
            package_weight=cls.extract_weight(name),
            brand=cls.detect_brand(name),
            pet_type=cls.detect_pet_type(name),
            is_medical=cls.detect_medical(name),
            in_stock=in_stock,
        )

    @classmethod
    def parse_product(
        cls,
        name: Optional[str],
        price_text: Optional[str],
        real_price_text: Optional[str] = None,
        discount_text: Optional[str] = None,
        pum_text: Optional[str] = None,
        card_text: str = "",
    ) -> Optional[ParsedProduct]:
        """
        Primary parser: works on the individual fields Rappi exposes per card
        through data-qa attributes (product-name, product-price, ...).
        """
        name = " ".join((name or "").split())
        price_current = cls.parse_price_text(price_text)
        if not name or price_current is None:
            return None
        unit_price, unit_measure = cls.parse_unit_price(pum_text)
        in_stock = not any(w in (card_text or "").lower() for w in cls.OUT_OF_STOCK_WORDS)
        return cls._build(
            name,
            price_current,
            cls.parse_price_text(real_price_text),
            cls.parse_discount(discount_text),
            unit_price,
            unit_measure,
            in_stock,
        )

    @classmethod
    def parse_card(cls, card_lines: list[str]) -> Optional[ParsedProduct]:
        """
        Fallback parser for the raw text lines of a product card, used when the
        structured data-qa fields are missing (e.g. Rappi changes its markup).
        """
        filtered = [l.strip() for l in card_lines or [] if l.strip() and l.strip().lower() not in cls.UI_NOISE]
        if not filtered:
            return None

        full_text = " ".join(filtered)
        in_stock = not any(w in full_text.lower() for w in cls.OUT_OF_STOCK_WORDS)

        prices = [p for p in (cls.parse_price_text(l) for l in filtered if cls.PRICE_PATTERN.search(l)) if p]
        if not prices:
            return None

        discount_pct = next((d for d in (cls.parse_discount(l) for l in filtered) if d is not None), None)
        unit_price, unit_measure = next(
            (u for u in (cls.parse_unit_price(l) for l in filtered) if u[0] is not None), (None, None)
        )

        non_price_lines = [
            l for l in filtered
            if not cls.PRICE_PATTERN.search(l)
            and not cls.DISCOUNT_PATTERN.search(l)
            and not cls.UNIT_PRICE_PATTERN.search(l)
        ]
        name = max(non_price_lines, key=len) if non_price_lines else filtered[-1]

        return cls._build(
            name,
            prices[0],
            prices[1] if len(prices) > 1 else None,
            discount_pct,
            unit_price,
            unit_measure,
            in_stock,
        )
