"""Draft a Hindi story with a local Ollama model."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from ollama_client import chat

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.environ.get("PIPELINE_CONFIG", ROOT / "config.json"))
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
PROJECT = Path(CONFIG["project_dir"])


def clean(text: str) -> str:
    text = re.sub(r"^```(?:markdown|md)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return text.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--minutes", type=float, default=5)
    parser.add_argument("--chapters", type=int, default=5)
    parser.add_argument("--instructions", default="")
    parser.add_argument("--model", default=CONFIG["story_model"])
    parser.add_argument("--out", default=str(PROJECT / "story.md"))
    args = parser.parse_args()

    words = int(args.minutes * 130)
    extra = f"\nअतिरिक्त निर्देश:\n{args.instructions.strip()}\n" if args.instructions.strip() else ""
    system = (
        "आप एक अनुभवी हिंदी कहानीकार और पटकथा लेखक हैं। "
        "आप केवल शुद्ध, स्वाभाविक हिंदी (देवनागरी) में लिखते हैं। "
        "उपयोगकर्ता के विषय और निर्देशों का ठीक-ठीक पालन करते हैं। "
        "विषय से असंबंधित शैली, संदेश या उपकथा अपने से नहीं जोड़ते। "
        "भावनात्मक, सिनेमाई और सरल भाषा लिखते हैं।"
    )
    user = f"""
एक काल्पनिक हिंदी कहानी लिखें।

विषय: {args.topic}
लक्ष्य लंबाई: लगभग {words} शब्द (लगभग {args.minutes:g} मिनट का नैरेशन)।
{extra}
संरचना:
- कुल {args.chapters} अध्याय; हर अध्याय में कहानी को आगे बढ़ाने वाला एक स्पष्ट मोड़।
- मुख्य पात्र, उनकी परिस्थिति और केंद्रीय समस्या विषय और निर्देशों से ही लें।
- हर अध्याय के अंत में अगले अध्याय को जानने की उत्सुकता छोड़ें।
- कहानी का संतोषजनक अंत करें; कोई वाक्य अधूरा न छोड़ें।
- केवल वही ठोस विवरण जोड़ें जो कहानी की दुनिया और निर्देशों के अनुरूप हों।

नियम:
- असली व्यक्तियों, कंपनियों या ब्रांडों के नाम न रखें।
- विषय से असंबंधित शैली, संदेश या उपकथा न जोड़ें।
- भाषा सरल, भावनात्मक और संवाद-प्रधान हो।
- केवल कहानी लौटाएँ, कोई अतिरिक्त चर्चा नहीं।
"""
    print(f"[story] model={args.model} target={words} words")
    text = chat(
        CONFIG["ollama_url"],
        args.model,
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        num_predict=min(8192, max(1024, words * 3)),
        temperature=0.85,
    )
    text = clean(text)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    actual = len(re.findall(r"\S+", text))
    print(f"[story] saved {out} ({actual} words)")
    if actual < words * 0.7:
        print("[story] warning: output is shorter than the target; consider regenerating or expanding.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
