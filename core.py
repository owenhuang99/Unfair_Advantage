import os, re, json, datetime, hashlib, typing as T
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse
from collections import deque

import pandas as pd
import requests
from bs4 import BeautifulSoup
import trafilatura
from dotenv import load_dotenv
from openai import OpenAI

# Load config
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_WITH_WEB = os.getenv("MODEL_WITH_WEB", "gpt-4o-mini")     # has web tool on eligible accounts
MODEL_FALLBACK = os.getenv("MODEL_FALLBACK", "gpt-4o-mini")    # local LLM fallback
MODEL_FOR_CARDS = os.getenv("MODEL_FOR_CARDS", "gpt-4o-mini")  # lightweight, cheap

MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", "8000"))       # cap article text sent to LLM

# TAXONOMY_PATH  = os.getenv("TAXONOMY_PATH", "taxonomy.json")    # where allowed lists persist
# CSV_PATH       = os.getenv("CSV_PATH", "links_store.csv")       # where your DataFrame persists


CSV_PATH = "data/links_store.csv"
TAXONOMY_PATH = "data/taxonomy.json"
LINKS_CSV = "data/links_store.csv"
CARDS_CSV = "data/cards_store.csv"



DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0"
}

STRICT_JSON_RULES = (
    "Return STRICT JSON with keys: "
    '["title","author","publish_date","categories","tags","tldr","language","citations","confidence_notes"]. '
    "categories=1–3 short labels; tags=5–12 keywords; tldr=3–6 crisp bullets; "
    "language=two-letter ISO code; citations=list of {title,url}; "
    "confidence_notes=1–2 short sentences. No markdown—JSON only."
)



## Build streamlit connection:
def process_new_link(url: str) -> dict:
    """Main function to process a new link - called from Streamlit"""
    try:
        # 1. Analyze link and get metadata
        rec, row, df = ingest_or_fetch(url)
        
        # 2. Generate flashcards 
        df_cards = generate_cards_for_url(
            url_canonical=row["url_canonical"],
            n=5,
            regenerate=False
        )
        
        return {
            "success": True,
            "link_data": row,
            "cards": df_cards.to_dict('records') if not df_cards.empty else [],
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "link_data": None, 
            "cards": None,
            "error": str(e)
        }

def get_flashcard_for_review(url: str = None) -> dict:
    """Get next flashcard for review - called from Streamlit"""
    try:
        if url:
            # Get cards for specific URL
            df = load_unlearned_cards(url)
        else:
            # Get all unlearned cards
            df = load_all_unlearned_cards()
            
        if df.empty:
            return {"success": True, "has_cards": False}
            
        # Get first unlearned card
        card = df.iloc[0].to_dict()
        return {
            "success": True,
            "has_cards": True,
            "card": card
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def mark_card_status(card_id: str, learned: bool) -> bool:
    """Mark card as learned/unlearned - called from Streamlit"""
    try:
        df = _ensure_cards_csv(CARDS_CSV)
        idx = df.index[df["card_id"] == card_id]
        if len(idx) > 0:
            df.loc[idx, "learned"] = learned
            _save_cards_df(df, CARDS_CSV)
        return True
    except:
        return False

def get_next_flashcard(current_card_id: str = None) -> dict:
    """Get next unlearned flashcard, considering the current card"""
    df = load_all_unlearned_cards()
    if df.empty:
        return {"success": True, "has_cards": False}
    
    if current_card_id:
        # Move current card to end if it exists and Review Later was clicked
        cards = df.to_dict('records')
        if len(cards) > 1:
            current_idx = df.index[df['card_id'] == current_card_id].tolist()
            if current_idx:
                cards.append(cards.pop(current_idx[0]))
    else:
        cards = df.sample(frac=1).to_dict('records')  # Shuffle if starting new session
    
    return {
        "success": True,
        "has_cards": True,
        "card": cards[0],
        "total_remaining": len(cards)
    }

# =========================
# Types
# =========================
@dataclass
class PageContent:
    url: str
    domain: str
    title: T.Optional[str]
    author: T.Optional[str]
    publish_date: T.Optional[str]
    text: str
    html_len: int
    text_len: int

# =========================
# Helpers: parsing & fetching
# =========================
def _best_bs4_parser():
    try:
        import lxml  # noqa
        return "lxml"
    except Exception:
        try:
            import html5lib  # noqa
            return "html5lib"
        except Exception:
            return "html.parser"

def _safe_json_loads(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {"error": "Non-JSON output", "raw": text[:1200]}

def _fetch_html(url: str) -> str:
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=25)
    r.raise_for_status()
    return r.text

def _guess_meta(soup: BeautifulSoup) -> dict:
    meta = {"title": None, "author": None, "publish_date": None}
    # title
    if soup.title and soup.title.string:
        meta["title"] = soup.title.string.strip()
    ogt = soup.find("meta", property="og:title")
    if ogt and ogt.get("content"):
        meta["title"] = ogt["content"].strip()
    # author
    for k in ["author", "article:author", "og:article:author"]:
        m = soup.find("meta", attrs={"name": k}) or soup.find("meta", attrs={"property": k})
        if m and m.get("content"):
            meta["author"] = m["content"].strip(); break
    # date
    for k in ["article:published_time", "og:published_time", "pubdate", "publish-date", "date"]:
        m = soup.find("meta", attrs={"name": k}) or soup.find("meta", attrs={"property": k})
        if m and m.get("content"):
            meta["publish_date"] = m["content"].strip(); break
    if meta["publish_date"] is None:
        t = soup.find("time")
        if t and (t.get("datetime") or t.text):
            meta["publish_date"] = (t.get("datetime") or t.text).strip()
    return meta

def extract_readable_text(url: str) -> PageContent:
    html = _fetch_html(url)
    text = (trafilatura.extract(html, include_comments=False, include_tables=False, favor_precision=True) or "").strip()

    if len(text) < 200:
        PARSER = _best_bs4_parser()
        soup = BeautifulSoup(html, PARSER)
        for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
            tag.extract()
        text = soup.get_text("\n", strip=True)

    PARSER = _best_bs4_parser()
    soup_full = BeautifulSoup(html, PARSER)
    meta = _guess_meta(soup_full)

    text = re.sub(r"\n{3,}", "\n\n", text)
    return PageContent(
        url=url,
        domain=urlparse(url).netloc,
        title=meta["title"],
        author=meta["author"],
        publish_date=meta["publish_date"],
        text=text,
        html_len=len(html or ""),
        text_len=len(text or "")
    )

# =========================
# Taxonomy persistence
# =========================
def load_taxonomy(path: str = TAXONOMY_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        return {"categories": [], "tags": []}
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # ensure keys
    data.setdefault("categories", [])
    data.setdefault("tags", [])
    return data

def save_taxonomy(categories: T.List[str], tags: T.List[str], path: str = TAXONOMY_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"categories": categories, "tags": tags}, f, ensure_ascii=False, indent=2)

# =========================
# Matching & evolving lists
# =========================
def _normalize_token(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def update_matches(candidates: T.List[str], allowed: T.List[str], max_k: int) -> T.Tuple[T.List[str], T.List[str]]:
    """
    Try to match candidates against allowed list.
    If no match found for a candidate, add it as a new allowed term.
    Returns (final_matches, updated_allowed_list).
    """
    allowed_norm = { _normalize_token(a): a for a in allowed }
    matches, updated_allowed = [], allowed.copy()
    seen = set()

    for c in candidates:
        if not isinstance(c, str):
            continue
        c_clean = c.strip()
        if not c_clean:
            continue
        c_norm = _normalize_token(c_clean)

        hit = None
        # exact
        if c_norm in allowed_norm:
            hit = allowed_norm[c_norm]
        else:
            # substring match either way
            for an_norm, raw in allowed_norm.items():
                if c_norm in an_norm or an_norm in c_norm:
                    hit = raw; break
        if hit:
            if hit not in seen:
                matches.append(hit); seen.add(hit)
        else:
            # new term → append to allowed
            if c_clean not in updated_allowed:
                updated_allowed.append(c_clean)
            if c_clean not in seen:
                matches.append(c_clean); seen.add(c_clean)

        if len(matches) >= max_k:
            break

    return matches, updated_allowed

# =========================
# LLM calls (web tool → local fallback)
# =========================
def analyze_link_with_web_tool(url: str, allowed_categories: T.List[str], allowed_tags: T.List[str]) -> dict:
    if not hasattr(client, "responses"):
        raise RuntimeError("responses_api_unavailable")

    user_prompt = (
        f"{STRICT_JSON_RULES}\n\n"
        f"When labeling categories and tags, prefer from the lists below when semantically appropriate.\n"
        f"Allowed categories: {json.dumps(allowed_categories[:50])}\n"
        f"Allowed tags: {json.dumps(allowed_tags[:200])}\n\n"
        f"Read this URL and summarize with citations: {url}"
    )

    resp = client.responses.create(
        model=MODEL_WITH_WEB,
        tools=[{"type": "web_search"}],
        input=[
            {"role": "system", "content": "You are a precise analyst that reads the provided URL using the web tool."},
            {"role": "user", "content": user_prompt}
        ],
    )
    output_text = getattr(resp, "output_text", getattr(resp, "output", ""))
    return _safe_json_loads(output_text)

def summarize_local_content(page: PageContent, allowed_categories: T.List[str], allowed_tags: T.List[str]) -> dict:
    payload = {
        "source_url": page.url,
        "detected_title": page.title,
        "detected_author": page.author,
        "detected_publish_date": page.publish_date,
        "article_text": page.text[:22_000],
        "allowed_categories": allowed_categories[:50],
        "allowed_tags": allowed_tags[:200]
    }
    if hasattr(client, "responses"):
        resp = client.responses.create(
            model=MODEL_FALLBACK,
            input=[
                {"role": "system", "content": STRICT_JSON_RULES},
                {"role": "user", "content": json.dumps(payload)}
            ],
        )
        output_text = getattr(resp, "output_text", getattr(resp, "output", ""))
        return _safe_json_loads(output_text)
    else:
        # very old fallback
        messages = [
            {"role": "system", "content": STRICT_JSON_RULES},
            {"role": "user", "content": json.dumps(payload)},
        ]
        cc = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return _safe_json_loads(cc.choices[0].message.content)

# =========================
# Public API: main function
# =========================
def analyze_link_plus(
    url: str,
    allowed_categories: T.List[str] = None,
    allowed_tags: T.List[str] = None,
    force_local: bool = False,
) -> dict:
    """
    Returns a normalized record (dict) and includes updated taxonomy under _taxonomy.
    Keys:
        fetched_at_utc, url, domain, headline, categories, tags, tldr (list),
        content_text, source_title, author, publish_date, _source, _taxonomy
    """
    assert url.startswith("http"), "Pass a valid http(s) URL."
    allowed_categories = allowed_categories or []
    allowed_tags = allowed_tags or []

    # parse locally first so you can verify and fall back if needed
    page = extract_readable_text(url)

    # LLM metadata
    try:
        if force_local:
            raise RuntimeError("forced_local")
        llm_data = analyze_link_with_web_tool(url, allowed_categories, allowed_tags)
        mode = "openai_web_tool"
        model_used = MODEL_WITH_WEB
    except Exception:
        if page.text_len < 200:
            raise RuntimeError("Could not extract enough text; page may be paywalled or script-rendered.")
        llm_data = summarize_local_content(page, allowed_categories, allowed_tags)
        mode = "local_fallback"
        model_used = MODEL_FALLBACK

    # normalize fields
    fetched_at_utc = datetime.datetime.utcnow().isoformat() + "Z"
    raw_categories = llm_data.get("categories") or []
    raw_tags = llm_data.get("tags") or []
    tldr = llm_data.get("tldr") or []

    # TLDR as list
    if isinstance(tldr, str):
        parts = [p.strip(" -•\t") for p in re.split(r"[\n•\-]+", tldr) if p.strip()]
        tldr = parts[:6] if parts else [llm_data.get("tldr", "")]

    # evolve taxonomy
    categories, updated_categories = update_matches(raw_categories, allowed_categories, max_k=3)
    tags, updated_tags = update_matches(raw_tags, allowed_tags, max_k=12)

    record = {
        "fetched_at_utc": fetched_at_utc,
        "url": page.url,
        "domain": page.domain,
        "headline": (llm_data.get("title") or page.title or "").strip()[:300],
        "categories": categories,
        "tags": tags,
        "tldr": tldr,
        "content_text": page.text,    # full parsed text so you can verify LLM output
        "source_title": page.title,
        "author": llm_data.get("author") or page.author,
        "publish_date": llm_data.get("publish_date") or page.publish_date,
        "_source": {"mode": mode, "model": model_used},
        "_taxonomy": {
            "updated_categories": updated_categories,
            "updated_tags": updated_tags
        }
    }
    return record

## Store record incrementally in the CSV

# =========================
# URL canonicalization (for stable dedupe)
# =========================
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

_STRIP_PARAMS = {
    "utm_source","utm_medium","utm_campaign","utm_term","utm_content",
    "utm_name","utm_id","gclid","gclsrc","fbclid","mc_cid","mc_eid"
}

def canonicalize_url(url: str) -> str:
    """
    Normalize URL for dedupe:
    - lowercase scheme/host
    - remove common tracking params
    - sort remaining query params
    - strip trailing slash (except root)
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    # normalize trailing slash
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    # clean & sort query
    q = []
    for k, v in parse_qsl(parsed.query, keep_blank_values=True):
        if k.lower() in _STRIP_PARAMS:
            continue
        q.append((k, v))
    q.sort(key=lambda kv: kv[0].lower())
    query = urlencode(q, doseq=True)

    canon = urlunparse((scheme, netloc, path, "", query, ""))
    return canon

# =========================
# DataFrame Store (CSV cache with dedupe by url_canonical)
# =========================
COLUMNS = [
    "fetched_at_utc","url","url_canonical","domain","headline",
    "categories","tags","tldr","content_text","source_title","author","publish_date"
]

def init_store() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    # add any missing columns (for backward compatibility)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    # backfill url_canonical if missing/empty
    if df["url_canonical"].isna().any() or (df["url_canonical"] == "").any():
        df["url_canonical"] = df.apply(
            lambda r: canonicalize_url(r["url"]) if pd.isna(r["url_canonical"]) or r["url_canonical"] == "" else r["url_canonical"],
            axis=1
        )
    return df[COLUMNS]

def save_csv(df: pd.DataFrame, path: str = CSV_PATH) -> None:
    df2 = df.copy()
    # lists -> JSON strings for portability
    for col in ["categories","tags","tldr"]:
        if col in df2.columns:
            df2[col] = df2[col].apply(lambda x: x if isinstance(x, str) else json.dumps(x, ensure_ascii=False))
    df2.to_csv(path, index=False)

def load_csv(path: str = CSV_PATH) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return init_store()
    df = pd.read_csv(path)
    # restore lists
    for col in ["categories","tags","tldr"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda s: json.loads(s) if isinstance(s, str) and s.startswith("[") else ([] if pd.isna(s) else s))
    df = _ensure_columns(df)
    return df

def append_record(df: pd.DataFrame, record: dict) -> pd.DataFrame:
    row = {
        "fetched_at_utc": record.get("fetched_at_utc"),
        "url": record.get("url"),
        "url_canonical": canonicalize_url(record.get("url","")),
        "domain": record.get("domain"),
        "headline": record.get("headline"),
        "categories": record.get("categories"),
        "tags": record.get("tags"),
        "tldr": record.get("tldr"),
        "content_text": record.get("content_text"),
        "source_title": record.get("source_title"),
        "author": record.get("author"),
        "publish_date": record.get("publish_date"),
    }
    return pd.concat([df, pd.DataFrame([row])], ignore_index=True)

def get_cached_row(df: pd.DataFrame, url: str) -> T.Optional[dict]:
    canon = canonicalize_url(url)
    hits = df[df["url_canonical"] == canon]
    if len(hits) == 0:
        return None
    rec = hits.iloc[0].to_dict()
    # ensure list types for convenience
    for col in ["categories","tags","tldr"]:
        v = rec.get(col)
        if isinstance(v, str):
            try:
                rec[col] = json.loads(v) if v.startswith("[") else [v]
            except Exception:
                rec[col] = [v]
    return rec

# =========================
# Orchestrator: ingest OR fetch from cache
# =========================
def ingest_or_fetch(
    url: str,
    taxonomy_path: str = TAXONOMY_PATH,
    csv_path: str = CSV_PATH,
    force_reingest: bool = False,
) -> T.Tuple[dict, pd.DataFrame]:
    """
    If canonical URL exists in CSV, return the cached row (and skip LLM).
    Else run analyze_link_plus(), update taxonomy JSON, append 1 row to CSV, and return the new row.
    Returns: (row_as_dict, updated_df)
    """
    # 0) load CSV (cache) and taxonomy
    df = load_csv(csv_path)
    tax = load_taxonomy(taxonomy_path)
    tax.setdefault("categories", [])
    tax.setdefault("tags", [])

    # 1) cached?
    if not force_reingest:
        cached = get_cached_row(df, url)
        if cached is not None:
            rec = {}
            return rec, cached, df  # nothing else to do

    # 2) not cached → analyze
    rec = analyze_link_plus(
        url,
        allowed_categories=tax["categories"],
        allowed_tags=tax["tags"]
    )

    # 3) update taxonomy (evolving lists)
    tax["categories"] = rec["_taxonomy"]["updated_categories"]
    tax["tags"] = rec["_taxonomy"]["updated_tags"]
    save_taxonomy(tax["categories"], tax["tags"], taxonomy_path)

    # 4) append to CSV cache
    df = append_record(df, rec)
    save_csv(df, csv_path)

    # 5) return a compact dict consistent with CSV row formatting
    row = {
        "fetched_at_utc": rec["fetched_at_utc"],
        "url": rec["url"],
        "url_canonical": canonicalize_url(rec["url"]),
        "domain": rec["domain"],
        "headline": rec["headline"],
        "categories": rec["categories"],
        "tags": rec["tags"],
        "tldr": rec["tldr"],
        "content_text": rec["content_text"],
        "source_title": rec["source_title"],
        "author": rec["author"],
        "publish_date": rec["publish_date"],
    }
    return rec, row, df


# =========================
# MVP Flashcards (Single CSV + Swipe Queue)
# =========================

import os, re, json, hashlib, datetime, typing as T
from pathlib import Path
from collections import deque

import pandas as pd
from dotenv import load_dotenv

# ---- OpenAI client ----
load_dotenv()
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# =========================
# CSV schema
# =========================
CARD_COLUMNS = [
    "card_id",         # pk (sha1 of url_canonical + "\n" + normalized_question)
    "url_canonical",   # article key
    "question",
    "answer",
    "learned",         # bool
    "created_at_utc"   # ISO str
]

def _ensure_cards_csv(path: str = CARDS_CSV) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        df = pd.DataFrame(columns=CARD_COLUMNS)
        df.to_csv(path, index=False)
        return df
    df = pd.read_csv(path)
    # Backward/robust handling
    for col in CARD_COLUMNS:
        if col not in df.columns:
            df[col] = None
    # Coerce learned -> bool
    if "learned" in df.columns:
        df["learned"] = df["learned"].apply(lambda x: bool(x) if isinstance(x, (bool,)) else (str(x).lower() == "true"))
    return df[CARD_COLUMNS]

def _save_cards_df(df: pd.DataFrame, path: str = CARDS_CSV) -> None:
    df2 = df.copy()
    df2.to_csv(path, index=False)

# =========================
# Utilities
# =========================
def _normalize_question(q: str) -> str:
    q = (q or "").strip()
    # collapse spaces, strip trailing ?
    q = re.sub(r"\s+", " ", q)
    return q

def _card_id(url_canonical: str, question: str) -> str:
    base = f"{url_canonical}\n{_normalize_question(question)}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]

def _utc_now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"

def _safe_json_loads(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {"error": "Non-JSON", "raw": text[:1200]}

# =========================
# LLM: generate Q&A from content_text
# =========================
_SYSTEM_PROMPT = (
    "You generate concise, factual Q&A flashcards from text. Avoid trivia and ambiguity. "
    "Prefer concrete facts, key definitions, mechanisms, comparisons, and takeaways. "
    "Keep questions ≤ 140 characters, answers ≤ 240 characters."
)

_USER_TEMPLATE = """From the text below, produce 3–6 Q&A flashcards that capture the core facts/concepts.
Return STRICT JSON only:
{"cards":[{"q":"...","a":"..."}]}

Text (may be truncated):
{TEXT}
"""

def _call_llm_for_cards(content_text: str, model: str = MODEL_FOR_CARDS) -> T.List[T.Dict[str, str]]:
    # Use Responses API if available
    payload = _USER_TEMPLATE.replace("{TEXT}", (content_text or "")[:MAX_TEXT_CHARS])
    if hasattr(client, "responses"):
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": payload}
            ],
        )
        out = getattr(resp, "output_text", getattr(resp, "output", ""))
        data = _safe_json_loads(out)
    else:
        # very old fallback
        cc = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": _SYSTEM_PROMPT},
                      {"role": "user", "content": payload}]
        )
        data = _safe_json_loads(cc.choices[0].message.content)

    cards = data.get("cards", [])
    # lightweight validation & cleaning
    clean = []
    seen_q = set()
    for c in cards:
        q = _normalize_question(str(c.get("q", "")).strip())
        a = str(c.get("a", "")).strip()
        if not q or not a:
            continue
        if len(q) > 200 or len(a) > 500:
            # discard egregiously long pairs (model might go verbose)
            continue
        if q.lower() in seen_q:
            continue
        seen_q.add(q.lower())
        clean.append({"q": q, "a": a})
    return clean[:6]  # cap to 6


def generate_cards_for_url(
    url_canonical: str,
    n: int = 5,
    *,
    regenerate: bool = False,
    return_scope: str = "all",      # "all" or "url"
    reset_learn: bool = False,
    reset_learn_scope: str = "all", # "url" or "all"
) -> pd.DataFrame:
    """
    Idempotent by default.
    - Optional resets before generation:
        * reset_learn=True & reset_learn_scope="url" -> set learned=False for this URL only
        * reset_learn=True & reset_learn_scope="all" -> set learned=False for ALL rows
    - If cards for `url_canonical` already exist and `regenerate=False`, skip LLM and just return existing.
    - If no cards exist yet (new URL), call LLM and upsert.
    - Returns either the full cards DataFrame ("all") or only rows for this URL ("url").
    """
    if not url_canonical or not isinstance(url_canonical, str):
        raise ValueError("url_canonical must be a non-empty string.")
    if return_scope not in ("all", "url"):
        raise ValueError("return_scope must be 'all' or 'url'.")
    if reset_learn_scope not in ("url", "all"):
        raise ValueError("reset_learn_scope must be 'url' or 'all'.")

    # Optional reset(s)
    if reset_learn:
        reset_learned(url_canonical, reset_learn_scope)

    df = _ensure_cards_csv(CARDS_CSV)

    # Fast path: URL already present -> skip generation unless forced
    if not regenerate and (df["url_canonical"] == url_canonical).any():
        return df if return_scope == "all" else df[df["url_canonical"] == url_canonical].copy()

    # Otherwise, try to generate
    rec, row, df_full = ingest_or_fetch(url_canonical)
    pairs = _call_llm_for_cards(row["content_text"])
    if not pairs:
        # Nothing generated; just return whatever we have already
        df = _ensure_cards_csv(CARDS_CSV)
        return df if return_scope == "all" else df[df["url_canonical"] == url_canonical].copy()

    existing_ids = set(df["card_id"].astype(str).tolist())
    rows_to_add = []
    now_iso = _utc_now_iso()
    count_added = 0

    for pair in pairs:
        if count_added >= max(1, n):  # ensure at least 1 if any generated
            break
        q, a = pair["q"], pair["a"]
        cid = _card_id(url_canonical, q)
        if cid in existing_ids:
            continue
        rows_to_add.append({
            "card_id": cid,
            "url_canonical": url_canonical,
            "question": q,
            "answer": a,
            "learned": False,
            "created_at_utc": now_iso
        })
        count_added += 1

    if rows_to_add:
        df = pd.concat([df, pd.DataFrame(rows_to_add)], ignore_index=True)
        _save_cards_df(df, CARDS_CSV)

    df = _ensure_cards_csv(CARDS_CSV)
    return df if return_scope == "all" else df[df["url_canonical"] == url_canonical].copy()


def load_unlearned_cards(url_canonical: str) -> pd.DataFrame:
    df = _ensure_cards_csv(CARDS_CSV)
    mask = (df["url_canonical"] == url_canonical) & (~df["learned"])
    return df[mask].copy()

def start_session(url_canonical: str, shuffle: bool = True) -> deque:
    """
    Returns a deque of dicts: [{"card_id","question","answer"}, ...] for unlearned cards.
    """
    df = load_unlearned_cards(url_canonical)
    print(f"Found {len(df)} unlearned cards for {url_canonical}")
    cards = df[["card_id","question","answer"]].to_dict(orient="records")
    if shuffle and len(cards) > 1:
        import random
        random.shuffle(cards)
    return deque(cards)

def swipe_left(queue: deque) -> None:
    """
    "Review again": move the current card to the end of the queue.
    No persistence change.
    """
    if not queue:
        return
    queue.append(queue.popleft())

def swipe_right(queue: deque, card_id: str) -> None:
    """
    "I know it": mark learned=True in CSV, then remove from the queue.
    """
    if not queue:
        return
    current = queue[0]
    if current["card_id"] != card_id:
        # guard: if caller passed mismatched card_id, align to current
        card_id = current["card_id"]

    # persist learned=True
    df = _ensure_cards_csv(CARDS_CSV)
    idx = df.index[df["card_id"] == card_id]
    if len(idx) > 0:
        df.loc[idx, "learned"] = True
        _save_cards_df(df, CARDS_CSV)

    # remove from queue
    queue.popleft()

def count_unlearned(url_canonical: str) -> int:
    return len(load_unlearned_cards(url_canonical))


def reset_learned(url_canonical: str, reset_learn_scope: str = "url") -> int:
    """
    Set learned=False based on scope.
      - reset_learn_scope == "url": only rows for the given url_canonical
      - reset_learn_scope == "all": all rows in the CSV

    Returns the number of rows reset.
    """
    if reset_learn_scope not in ("url", "all"):
        raise ValueError("reset_learn_scope must be 'url' or 'all'.")

    df = _ensure_cards_csv(CARDS_CSV)
    if df.empty:
        return 0

    if reset_learn_scope == "all":
        n = len(df)
        if n > 0:
            df["learned"] = False
            _save_cards_df(df, CARDS_CSV)
        return n

    # scope == "url"
    mask = (df["url_canonical"] == url_canonical)
    n = int(mask.sum())
    if n > 0:
        df.loc[mask, "learned"] = False
        _save_cards_df(df, CARDS_CSV)
    return n



# =========================
# Convenience helpers
# =========================
def url_exists_in_cards(url_canonical: str, path: str = CARDS_CSV) -> bool:
    df = _ensure_cards_csv(path)
    return bool((df["url_canonical"] == url_canonical).any())

def get_cards_for_url(url_canonical: str, path: str = CARDS_CSV) -> pd.DataFrame:
    df = _ensure_cards_csv(path)
    return df[df["url_canonical"] == url_canonical].copy()

def load_all_unlearned_cards() -> pd.DataFrame:
    df = _ensure_cards_csv(CARDS_CSV)
    if df.empty:
        return df.copy()
    return df[~df["learned"]].copy()

from ipywidgets import Button, HBox, VBox, HTML
from IPython.display import display
from collections import deque

def run_widget_session(url_canonical, shuffle=True, learn_all: bool = False):
    """
    Round-based review:
      - 'Review again' defers the card to the next round (again_q).
      - Deferred cards won't reappear until the next round.
      - If learn_all=True, review unlearned cards across ALL URLs; else only for url_canonical.
    """
    # Build initial queue from unlearned cards
    if learn_all:
        df = load_all_unlearned_cards()
        scope_label = "all URLs"
    else:
        df = load_unlearned_cards(url_canonical)
        scope_label = f"{url_canonical}"

    print(f"Found {len(df)} unlearned cards for {scope_label}")
    cards = df[["card_id", "question", "answer"]].to_dict(orient="records")
    if shuffle and len(cards) > 1:
        import random
        random.shuffle(cards)

    # Two-queue scheduler
    main_q = deque(cards)   # current round
    again_q = deque()       # next round
    round_idx = 1
    total_start = len(cards)

    # UI elements
    title = HTML("<h3>Flashcard Session</h3>")
    subtitle = HTML("")
    q_html = HTML("")
    a_html = HTML("")
    btn_reveal = Button(description="Reveal answer")
    btn_know   = Button(description="I know it 👍", button_style="success")
    btn_review = Button(description="Review again 🔁", button_style="warning")

    container = VBox([title, subtitle, q_html, a_html, HBox([btn_reveal, btn_know, btn_review])])

    def update_subtitle():
        subtitle.value = (
            f"<div style='color:#666'>Scope: {scope_label} • Round {round_idx} • "
            f"{len(main_q)} left in this round"
            f"{' • ' + str(len(again_q)) + ' deferred' if len(again_q) else ''}"
            f"{f' • {total_start} total' if total_start else ''}"
            f"</div>"
        )

    def rollover_if_needed():
        nonlocal main_q, again_q, round_idx
        if not main_q and again_q:
            main_q = again_q
            again_q = deque()
            round_idx += 1

    def disable_all():
        btn_reveal.disabled = True
        btn_know.disabled = True
        btn_review.disabled = True

    def render():
        rollover_if_needed()
        update_subtitle()

        if not main_q:
            q_html.value = "<b>All cards learned or deferred round(s) completed. 🎉</b>"
            a_html.value = ""
            disable_all()
            return

        card = main_q[0]
        q_html.value = f"<b>Question</b><div style='margin-top:4px'>{card['question']}</div>"
        a_html.value = "<i>(click 'Reveal answer')</i>"

    def on_reveal(_):
        if not main_q: return
        card = main_q[0]
        a_html.value = f"<b>Answer</b><div style='margin-top:6px'>{card['answer']}</div>"

    def on_know(_):
        # Persist learned=True and remove from current round
        if not main_q: return
        card = main_q[0]
        swipe_right(main_q, card["card_id"])  # persists and pops left from main_q
        render()

    def on_review(_):
        if not main_q: return
        # Defer current card to next round: move from main_q -> again_q
        card = main_q.popleft()
        again_q.append(card)
        render()

    btn_reveal.on_click(on_reveal)
    btn_know.on_click(on_know)
    btn_review.on_click(on_review)

    display(container)
    render()

