import pytest

from src.parser import ProductParser as P


@pytest.mark.parametrize("raw,expected", [
    ("115.750,00", 115750.0),
    ("264.505", 264505.0),
    ("$\xa018.585,00", 18585.0),
    ("1.234,5", 1234.5),
    ("115,750", 115750.0),
    ("", None),
    ("abc", None),
])
def test_clean_cop_price(raw, expected):
    assert P.clean_cop_price(raw) == expected


def test_parse_product_structured_fields_with_discount():
    p = P.parse_product(
        "Hill's Comida Perro Adulto Science Diet Small Bites 6.8 kg",
        "$\xa0264.505,00", "$\xa0293.895,00", "10%", "(38.88/g)",
    )
    assert p.price_current == 264505.0
    assert p.price_regular == 293895.0
    assert p.discount_pct == 10.0
    assert (p.unit_price_value, p.unit_measure) == (38.88, "g")
    assert p.brand == "Hill's" and p.pet_type == "Dog" and not p.is_medical
    assert p.package_weight == "6.8 kg"


def test_discount_is_derived_when_badge_missing():
    p = P.parse_product("Royal Canin Renal Gato 2 kg", "$ 90.000", "$ 100.000")
    assert p.discount_pct == 10.0
    assert p.is_medical and p.pet_type == "Cat"


def test_regular_price_not_higher_than_current_is_dropped():
    p = P.parse_product("Pedigree Adulto 4 kg", "$ 50.000", "$ 50.000")
    assert p.price_regular is None and p.discount_pct is None


def test_parse_product_rejects_missing_name_or_price():
    assert P.parse_product("", "$ 10.000") is None
    assert P.parse_product("Hills", None) is None


def test_out_of_stock_detected_from_card_text():
    p = P.parse_product("Hills k/d Perro", "$ 10.000", card_text="Hills k/d\nAgotado")
    assert p.in_stock is False


@pytest.mark.parametrize("text,expected", [
    ("Hills concentrado perro adulto", "Dog"),           # 'concentrado' must not hit 'cat'
    ("alimento humedo en lata para cachorro", "Dog"),
    ("Hill's Science Diet Canine Small Paws", "Dog"),
    ("Royal Canin Gastrointestinal Gato", "Cat"),
    ("Arena sanitaria multiuso", "Unknown / General"),
    ("Snack perro y gato", "Dog & Cat"),
])
def test_detect_pet_type(text, expected):
    assert P.detect_pet_type(text) == expected


def test_legacy_parse_card_fallback():
    cards = [
        (['Agregar', '0', '$ 115.750,00', '(57.88/g)', 'Hills Science Diet Small&Mini Perro Adulto Raza Pequeña 2 Kg'],
         115750.0, None, "2 Kg"),
        (['Agregar', '0', '$ 264.505,00', '$ 293.895,00', '10%', '(38.88/g)',
          "Hill's Comida Perro Adulto Science Diet Small Bites"], 264505.0, 293895.0, None),
        (['Agregar', '0', '$ 340.000,00', 'Royal Canin Veterinary Diet Gastrointestinal Gato 2 kg'],
         340000.0, None, "2 kg"),
    ]
    for lines, price, regular, weight in cards:
        p = P.parse_card(lines)
        assert p is not None
        assert p.price_current == price and p.price_regular == regular and p.package_weight == weight
    assert P.parse_card(['Agregar', '0']) is None


@pytest.mark.parametrize("a,b", [
    ("Hill's Comida Perro Adulto Science Diet Small Bites 2 Kg", "Alimento Hills Science Diet Small Bites para Perros Adultos"),
    ("Royal Canin Gastrointestinal Gato", "ROYAL CANIN Gastrointestinal Felino 2kg"),
    ("Hill's Prescription Diet i/d Alimento Húmedo", "hills prescription diet i/d alimento humedo"),
])
def test_match_key_merges_wording_variants(a, b):
    assert P.match_key(a) == P.match_key(b)


@pytest.mark.parametrize("a,b", [
    ("Hills Prescription Diet k/d Gato", "Hills Prescription Diet i/d Gato"),
    ("Royal Canin Mini Adult Perro", "Royal Canin Medium Adult Perro"),
    ("Pro Plan Cachorro Raza Pequeña", "Pro Plan Adulto Raza Pequeña"),
    ("Hills Science Diet Gato Humedo", "Hills Science Diet Gato Seco"),
])
def test_match_key_keeps_distinct_products_apart(a, b):
    assert P.match_key(a) != P.match_key(b)


def test_match_key_keeps_strengths_and_strips_weights():
    assert P.match_key("Veta Dicrysticina (2.000.000 Ui)") != P.match_key("Veta Dicrysticina (6.000.000 Ui)")
    assert P.match_key("Proplan Veterinary Diets Canine Om X 7.5 Kl") == P.match_key("Proplan Veterinary Diets Canine Om X 2 Kg")


@pytest.mark.parametrize("query,name,expected", [
    ("vet life perro medicado", "Vet Life Alimento Para Perro Renal", True),
    ("vet life perro medicado", "Nobivac Kc (Tos Perreras) Fco X 1D", False),
    ("tierragro gato", "Kelcat Alimento Humedo Gatos Carne", True),
    ("hills perro", "Hill's Science Diet Canine Light 2 kg", True),
    ("zzqxw nonexistent product 9174", "Royal Canin Mini Adult", False),
])
def test_is_relevant(query, name, expected):
    assert P.is_relevant(query, name) is expected


@pytest.mark.parametrize("query,name", [
    ("pro plan veterinary gato", "Proplan Alimento Gatito Pouch"),
    ("tierragro perro", "Puppy Balance"),
    ("tierragro gato", "nutrapro Gatos/gatitos 7,5 Kg"),
])
def test_is_relevant_handles_variants(query, name):
    assert P.is_relevant(query, name)
