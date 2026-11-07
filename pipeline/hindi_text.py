"""Hindi text normalization for the narration voice.

Chatterbox reads raw digits and currency symbols inconsistently, so every
narration is converted to spoken Hindi before synthesis:

    ₹38,000      -> अड़तीस हज़ार रुपये
    ₹14,500      -> चौदह हज़ार पाँच सौ रुपये
    11.5%        -> ग्यारह दशमलव पाँच प्रतिशत
    ₹1.2 लाख     -> एक लाख बीस हज़ार रुपये
    ₹1.5 लाख     -> डेढ़ लाख रुपये
    EMI          -> ईएमआई
"""

from __future__ import annotations

import re
from decimal import Decimal

NUM_0_99 = {
    0: "शून्य",
    1: "एक",
    2: "दो",
    3: "तीन",
    4: "चार",
    5: "पाँच",
    6: "छह",
    7: "सात",
    8: "आठ",
    9: "नौ",
    10: "दस",
    11: "ग्यारह",
    12: "बारह",
    13: "तेरह",
    14: "चौदह",
    15: "पंद्रह",
    16: "सोलह",
    17: "सत्रह",
    18: "अठारह",
    19: "उन्नीस",
    20: "बीस",
    21: "इक्कीस",
    22: "बाईस",
    23: "तेईस",
    24: "चौबीस",
    25: "पच्चीस",
    26: "छब्बीस",
    27: "सत्ताईस",
    28: "अट्ठाईस",
    29: "उनतीस",
    30: "तीस",
    31: "इकतीस",
    32: "बत्तीस",
    33: "तैंतीस",
    34: "चौंतीस",
    35: "पैंतीस",
    36: "छत्तीस",
    37: "सैंतीस",
    38: "अड़तीस",
    39: "उनतालीस",
    40: "चालीस",
    41: "इकतालीस",
    42: "बयालीस",
    43: "तैंतालीस",
    44: "चवालीस",
    45: "पैंतालीस",
    46: "छियालीस",
    47: "सैंतालीस",
    48: "अड़तालीस",
    49: "उनचास",
    50: "पचास",
    51: "इक्यावन",
    52: "बावन",
    53: "तिरेपन",
    54: "चौवन",
    55: "पचपन",
    56: "छप्पन",
    57: "सत्तावन",
    58: "अट्ठावन",
    59: "उनसठ",
    60: "साठ",
    61: "इकसठ",
    62: "बासठ",
    63: "तिरेसठ",
    64: "चौंसठ",
    65: "पैंसठ",
    66: "छियासठ",
    67: "सड़सठ",
    68: "अड़सठ",
    69: "उनहत्तर",
    70: "सत्तर",
    71: "इकहत्तर",
    72: "बहत्तर",
    73: "तिहत्तर",
    74: "चौहत्तर",
    75: "पचहत्तर",
    76: "छिहत्तर",
    77: "सतहत्तर",
    78: "अठहत्तर",
    79: "उन्नासी",
    80: "अस्सी",
    81: "इक्यासी",
    82: "बयासी",
    83: "तिरासी",
    84: "चौरासी",
    85: "पचासी",
    86: "छियासी",
    87: "सत्तासी",
    88: "अट्ठासी",
    89: "नवासी",
    90: "नब्बे",
    91: "इक्यानवे",
    92: "बानवे",
    93: "तिरानवे",
    94: "चौरानवे",
    95: "पंचानवे",
    96: "छियानवे",
    97: "सत्तानवे",
    98: "अट्ठानवे",
    99: "निन्यानवे",
}

UNITS = ((10_000_000, "करोड़"), (100_000, "लाख"), (1_000, "हज़ार"))
CURRENCY_UNITS = {
    "लाख": Decimal(100_000),
    "करोड़": Decimal(10_000_000),
    "हज़ार": Decimal(1_000),
}
ORDINALS = (
    "पहला",
    "दूसरा",
    "तीसरा",
    "चौथा",
    "पाँचवाँ",
    "छठा",
    "सातवाँ",
    "आठवाँ",
    "नौवाँ",
    "दसवाँ",
)
ACRONYMS = {
    r"\bEMI\b": "ईएमआई",
    r"\bCIBIL\b": "सिबिल",
    r"\bKYC\b": "केवाईसी",
    r"\bGST\b": "जीएसटी",
    r"\bATM\b": "एटीएम",
    r"\bUPI\b": "यूपीआई",
    r"\bSIP\b": "एसआईपी",
    r"\bFD\b": "एफडी",
    r"\bRD\b": "आरडी",
    r"\bOTP\b": "ओटीपी",
}
CURRENCY_RE = re.compile(
    r"(?:₹|रु\.?|Rs\.?|INR)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)"
    r"(?:\s*(लाख|करोड़|हज़ार))?"
    r"(?:\s*(?:रुपये|रुपया|रुपए))?",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(r"([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*%")
UNIT_RE = re.compile(r"([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(लाख|करोड़|हज़ार)")
NUMBER_RE = re.compile(r"\d+(?:,\d+)*(?:\.\d+)?")
LIST_RE = re.compile(r"(?m)^(\s*)(\d{1,2})\.\s+")


def hindi_int(n: int) -> str:
    if n < 0:
        return "माइनस " + hindi_int(-n)
    if n < 100:
        return NUM_0_99[n]
    parts: list[str] = []
    for value, name in UNITS:
        if n >= value:
            q, n = divmod(n, value)
            parts.append(f"{hindi_int(q)} {name}")
    if n >= 100:
        q, n = divmod(n, 100)
        parts.append(("एक" if q == 1 else hindi_int(q)) + " सौ")
    if n:
        parts.append(NUM_0_99[n])
    return " ".join(parts)


def hindi_number(raw: str) -> str:
    raw = raw.replace(",", "").strip()
    if "." in raw:
        whole, frac = raw.split(".", 1)
        frac = frac.rstrip("0")
        whole_words = hindi_int(int(whole or "0"))
        if not frac:
            return whole_words
        if len(frac) <= 2:
            frac_words = hindi_int(int(frac))
        else:
            frac_words = " ".join(NUM_0_99[int(d)] for d in frac)
        return f"{whole_words} दशमलव {frac_words}"
    return hindi_int(int(raw or "0"))


def hindi_money(amount: Decimal) -> str:
    # Natural spoken forms for the amounts that appear most often.
    if amount == Decimal("150000"):
        return "डेढ़ लाख"
    if amount == Decimal("250000"):
        return "ढाई लाख"
    rounded = amount.to_integral_value()
    if amount == rounded:
        return hindi_int(int(rounded))
    return hindi_number(f"{amount.normalize():f}")


def _money_replacement(match: re.Match) -> str:
    raw = match.group(1)
    unit = match.group(2)
    amount = Decimal(raw.replace(",", ""))
    if unit:
        amount *= CURRENCY_UNITS[unit]
    return f"{hindi_money(amount)} रुपये"


def _percent_replacement(match: re.Match) -> str:
    return f"{hindi_number(match.group(1))} प्रतिशत"


def _unit_replacement(match: re.Match) -> str:
    amount = Decimal(match.group(1).replace(",", "")) * CURRENCY_UNITS[match.group(2)]
    return hindi_money(amount)


def _list_replacement(match: re.Match) -> str:
    number = int(match.group(2))
    word = ORDINALS[number - 1] if 1 <= number <= len(ORDINALS) else hindi_int(number)
    return f"{match.group(1)}{word} "


def normalize_for_tts(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[#*_`]+", "", text)

    for pattern, replacement in ACRONYMS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    text = LIST_RE.sub(_list_replacement, text)
    text = CURRENCY_RE.sub(_money_replacement, text)
    text = UNIT_RE.sub(_unit_replacement, text)
    text = PERCENT_RE.sub(_percent_replacement, text)
    text = NUMBER_RE.sub(lambda match: hindi_number(match.group(0)), text)

    text = text.replace("—", "। ").replace("–", ", ")
    text = text.replace("\n", "। ")
    text = re.sub(r"[:;]", "। ", text)
    text = text.replace(".", "।")
    text = re.sub(r"[“”\"]", "", text)
    text = re.sub(r"[()]", ", ", text)
    text = re.sub(r"([।!?])\1+", r"\1", text)
    text = re.sub(r"।\s*।+", "।", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,।!?])", r"\1", text)
    if text and text[-1] not in "।!?":
        text += "।"
    return text
