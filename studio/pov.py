"""POV Finance format: clean Indian 2D vector cartoon, recurring protagonist, source-story adaptation."""

from __future__ import annotations

from . import store

POV_STYLE_PREFIX = (
    "clean 2D vector cartoon still, flat cel shading, thin dark outlines, bright warm pastel palette, "
    "simple friendly faces, minimal detail, 2D explainer animation style, Indian middle-class homes, "
    "offices and banks, cinematic 16:9 composition, natural light, no text, no watermark"
)

POV_CHARACTER = (
    "the protagonist is Aman, a 32-year-old Indian man with short black hair, a short neatly trimmed "
    "beard, warm brown skin, simple friendly cartoon facial features, wearing a dark green polo shirt, "
    "dark jeans and a simple watch; keep the same face, hair, beard, green shirt and age consistent "
    "in every scene"
)

POV_NEGATIVE = (
    "photorealistic, 3D render, heavy shading, gritty texture, detailed skin, complex background, "
    "heavy black outlines, low quality, blurry, text, watermark, logo, signature, deformed, extra "
    "fingers, bad anatomy, duplicate person, twins, clone, repeated character, two men with the same "
    "face, extra people"
)

POV_PUBLISH = {
    "channel_name": "POV Finance India",
    "channel_tagline": "आपकी कहानी, आपका फैसला",
    "contact_email": "oshosheekhe@gmail.com",
    "hashtags": "#POVFinance #HindiKahani #PersonalFinance",
    "cta": "अगर कहानी पसंद आई तो लाइक कीजिए और अपना अनुभव कमेंट में लिखिए।",
    "pov": True,
}

POV_LLM = {
    "provider": "opencode-go",
    "model": "claude-haiku-5-5",
    "api_base": store.OPENCODE_GO_BASE,
}

POV_TTS_REFERENCE = "../models/piper/hindi_ref.wav"

POV_ADAPT_INSTRUCTIONS = """इस ब्लूप्रिंट को एक भारतीय POV फाइनेंस कहानी में बदलें।

नियम:
- पूरी कहानी दूसरे व्यक्ति "आप" में लिखें। पाठक ही कहानी का मुख्य पात्र है।
- भारतीय मध्यवर्गीय जीवन: भारतीय शहर, नौकरी, परिवार, दोस्त, समाज, रिश्ते और रोज़मर्रा की चिंताएँ।
- पैसा भारतीय संदर्भ में: ₹ राशि, सैलरी, EMI, होम लोन, EPF/PPF/NPS, SIP, म्यूचुअल फंड, बीमा, सोना, संपत्ति, बचत।
- अमेरिकी शब्द, 401k, Roth IRA, TSP, mortgage, dollar, Labor Day, Wisconsin जैसी बातें पूरी तरह हटा दें।
- संख्याएँ भारतीय सैलरी और खर्च के हिसाब से तर्कसंगत रखें; हर अध्याय में ठोस आँकड़े और फैसले दिखें।
- कहानी का भावनात्मक आर्क, मोड़ और सीख बनाए रखें, लेकिन सभी दृश्य और पात्र भारतीय बनाएँ।
- हर अध्याय "## अध्याय N: <शीर्षक>" से शुरू हो; अंतिम अध्याय में स्पष्ट, संतोषजनक अंत और एक practical सीख हो।
- उपदेश नहीं; सीख पात्र के फैसले और परिणाम से निकले।
- कहानी को चुनी हुई अवधि के नैरेशन के लिए लिखें, सरल, भावनात्मक, दृश्यात्मक हिंदी में।
"""


def apply_template(state: dict) -> dict:
    """Apply the POV Finance visual, voice, model and publishing defaults."""
    settings = state.setdefault("settings", {})
    image = settings.setdefault("image", {})
    image.update({
        "engine": "sdxl",
        "style_prefix": POV_STYLE_PREFIX,
        "character": POV_CHARACTER,
        "negative_prompt": POV_NEGATIVE,
        "protagonist_name": "Aman",
        "cast": {},
        "steps": 28,
        "cfg": 7.0,
        "sampler": "dpmpp_2m",
        "scheduler": "karras",
    })
    tts = settings.setdefault("tts", {})
    tts["reference"] = POV_TTS_REFERENCE
    llm = settings.setdefault("llm", {})
    llm.update(POV_LLM)
    publish = settings.setdefault("publish", {})
    publish.update(POV_PUBLISH)
    settings["protagonist"] = "Aman"
    settings["story_instructions"] = POV_ADAPT_INSTRUCTIONS
    settings["story_genre"] = "POV Finance"
    return state
