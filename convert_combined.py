"""
全大学サークルデータ → アプリ用 all_circles_data.js 変換スクリプト
早稲田 (waseda_circles.json) + 他大学 (multi_univ_circles.json) + PDF大学 (pdf_univ_circles.json) を統合
"""
import json, re, os
from collections import Counter

SRC_WASEDA = os.path.join(os.path.dirname(__file__), "waseda_circles.json")
SRC_MULTI   = os.path.join(os.path.dirname(__file__), "multi_univ_circles.json")
SRC_PDF     = os.path.join(os.path.dirname(__file__), "pdf_univ_circles.json")
DEST        = os.path.join(os.path.dirname(__file__), "all_circles_data.js")

# ジャンルキー → アプリカテゴリ・スコア
GENRE_MAP = {
    "baseball":               {"cats":["sports"],            "scores":{"sports":9,"culture":1,"tech":1,"social":5,"outdoor":2,"creative":1,"game":1},"intensity":"gachi","vibe":"bright","vertical":True},
    "football":               {"cats":["sports"],            "scores":{"sports":9,"culture":1,"tech":1,"social":6,"outdoor":2,"creative":1,"game":1},"intensity":"middle","vibe":"bright","vertical":False},
    "futsal":                 {"cats":["sports"],            "scores":{"sports":9,"culture":1,"tech":1,"social":6,"outdoor":2,"creative":1,"game":1},"intensity":"middle","vibe":"bright","vertical":False},
    "basketball":             {"cats":["sports"],            "scores":{"sports":9,"culture":1,"tech":1,"social":5,"outdoor":1,"creative":1,"game":1},"intensity":"middle","vibe":"bright","vertical":False},
    "tennis":                 {"cats":["sports"],            "scores":{"sports":8,"culture":1,"tech":1,"social":7,"outdoor":3,"creative":1,"game":1},"intensity":"middle","vibe":"bright","vertical":False},
    "volleyball":             {"cats":["sports"],            "scores":{"sports":8,"culture":1,"tech":1,"social":5,"outdoor":1,"creative":1,"game":1},"intensity":"middle","vibe":"bright","vertical":False},
    "golf":                   {"cats":["sports","outdoor"],  "scores":{"sports":7,"culture":1,"tech":1,"social":6,"outdoor":6,"creative":1,"game":1},"intensity":"yuru","vibe":"cool","vertical":False},
    "badminton":              {"cats":["sports"],            "scores":{"sports":8,"culture":1,"tech":1,"social":6,"outdoor":1,"creative":1,"game":1},"intensity":"middle","vibe":"cozy","vertical":False},
    "dance":                  {"cats":["culture"],           "scores":{"sports":4,"culture":10,"tech":1,"social":7,"outdoor":1,"creative":5,"game":1},"intensity":"middle","vibe":"cool","vertical":False},
    "martial-arts":           {"cats":["sports"],            "scores":{"sports":9,"culture":3,"tech":1,"social":4,"outdoor":1,"creative":1,"game":1},"intensity":"gachi","vibe":"cozy","vertical":True},
    "skiing":                 {"cats":["outdoor","sports"],  "scores":{"sports":6,"culture":1,"tech":1,"social":7,"outdoor":9,"creative":1,"game":1},"intensity":"yuru","vibe":"bright","vertical":False},
    "swimming":               {"cats":["sports"],            "scores":{"sports":8,"culture":1,"tech":1,"social":4,"outdoor":3,"creative":1,"game":1},"intensity":"middle","vibe":"cozy","vertical":False},
    "outdoor":                {"cats":["outdoor"],           "scores":{"sports":4,"culture":1,"tech":1,"social":8,"outdoor":10,"creative":1,"game":1},"intensity":"yuru","vibe":"bright","vertical":False},
    "music":                  {"cats":["culture"],           "scores":{"sports":1,"culture":10,"tech":1,"social":5,"outdoor":1,"creative":7,"game":1},"intensity":"middle","vibe":"cozy","vertical":False},
    "theater":                {"cats":["culture","creative"],"scores":{"sports":1,"culture":9,"tech":2,"social":5,"outdoor":1,"creative":9,"game":1},"intensity":"middle","vibe":"cool","vertical":False},
    "cinema":                 {"cats":["creative"],          "scores":{"sports":1,"culture":6,"tech":2,"social":5,"outdoor":1,"creative":9,"game":2},"intensity":"yuru","vibe":"cozy","vertical":False},
    "fine-art":               {"cats":["creative"],          "scores":{"sports":1,"culture":5,"tech":1,"social":4,"outdoor":1,"creative":10,"game":1},"intensity":"yuru","vibe":"cozy","vertical":False},
    "international-exchange": {"cats":["social"],            "scores":{"sports":2,"culture":3,"tech":2,"social":10,"outdoor":2,"creative":2,"game":1},"intensity":"yuru","vibe":"bright","vertical":False},
    "volunteer":              {"cats":["social"],            "scores":{"sports":1,"culture":1,"tech":2,"social":10,"outdoor":3,"creative":2,"game":1},"intensity":"yuru","vibe":"cozy","vertical":False},
    "technology":             {"cats":["tech"],              "scores":{"sports":1,"culture":1,"tech":10,"social":4,"outdoor":1,"creative":4,"game":5},"intensity":"gachi","vibe":"cool","vertical":False},
    "economy":                {"cats":["tech"],              "scores":{"sports":1,"culture":1,"tech":9,"social":5,"outdoor":1,"creative":3,"game":1},"intensity":"gachi","vibe":"cool","vertical":False},
    "language":               {"cats":["social"],            "scores":{"sports":1,"culture":3,"tech":3,"social":9,"outdoor":1,"creative":2,"game":1},"intensity":"middle","vibe":"bright","vertical":False},
}

GACHI_KW = ["全国大会","リーグ戦優勝","大会優勝","週3","週4","週5","ガチ","本格的","競技","東京六大学"]
YURU_KW  = ["週1","気軽","ゆるく","のんびり","自由参加","来れる時","マイペース","初心者大歓迎","初心者でも","敷居が低"]

# 大学別のカラー（タグ用）
UNIV_TAG_COLOR = {
    "早稲田大学":   "tag-purple",
    "法政大学":     "tag-blue",
    "東京理科大学": "tag-teal",
    "一橋大学":     "tag-gold",
    "明治大学":     "tag-pink",
    "立教大学":     "tag-purple",
    "青山学院大学": "tag-blue",
    "中央大学":     "tag-teal",
    "上智大学":     "tag-gold",
    "慶應義塾大学": "tag-pink",
    "東京大学":     "tag-gold",
}

def detect_intensity(pr_text, default):
    for kw in GACHI_KW:
        if kw in pr_text:
            return "gachi"
    for kw in YURU_KW:
        if kw in pr_text:
            return "yuru"
    return default

def detect_size(pr_text):
    if re.search(r"[1-9]\d{2,}名|100名以上|大規模", pr_text):
        return "large"
    if re.search(r"[1-5]\d名|少人数|小規模", pr_text):
        return "small"
    return "medium"

def detect_cost(pr_text):
    if re.search(r"合宿費|遠征費|道具代|費用が高|出費", pr_text):
        return "medium"
    if re.search(r"無料|費用なし|格安|費用は安", pr_text):
        return "low"
    return "medium"

def make_tags(genre_ja, intensity, inkare, univ_name):
    tags = []
    tags.append({"l": genre_ja, "c": "tag-teal"})
    if intensity == "gachi":
        tags.append({"l": "本気系", "c": "tag-pink"})
    elif intensity == "yuru":
        tags.append({"l": "ゆるめ", "c": "tag-gold"})
    if inkare:
        tags.append({"l": "インカレ", "c": "tag-blue"})
    color = UNIV_TAG_COLOR.get(univ_name, "tag-purple")
    tags.append({"l": univ_name, "c": color})
    return tags[:4]

def make_photo_key(image_url, circle_id):
    no_img = "waseda_no_image"
    if image_url and no_img not in image_url:
        return image_url
    return f"smc_ws{circle_id}/400/400"

def convert_waseda(raw_list, start_id=100):
    circles = []
    for i, c in enumerate(raw_list):
        gkey  = c.get("genre_key", "outdoor")
        ginfo = GENRE_MAP.get(gkey, GENRE_MAP["outdoor"])
        pr    = c.get("pr_text", "")
        catchcopy = c.get("catchcopy", "")

        intensity = detect_intensity(pr, ginfo["intensity"])
        size      = detect_size(pr)
        cost      = detect_cost(pr)
        img_url   = c.get("image_url", "")
        photo_key = make_photo_key(img_url, c["id"])

        sns_instagram = ""
        insta_match = re.search(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)/?', pr)
        if insta_match and "wasedaweekly" not in insta_match.group(0):
            sns_instagram = "@" + insta_match.group(1)
        twitter_match = re.search(r'https?://(?:www\.)?(?:twitter|x)\.com/([A-Za-z0-9_]+)/?', pr)
        sns_twitter = ""
        if twitter_match and "wasedaweekly" not in twitter_match.group(0):
            sns_twitter = "@" + twitter_match.group(1)

        desc = ""
        if pr and len(pr) > 20:
            first_sent = re.split(r'[。\n]', pr)[0].strip()
            if len(first_sent) > 15:
                desc = first_sent[:120] + ("…" if len(first_sent) > 120 else "")
        if not desc:
            desc = catchcopy[:120] if catchcopy else "詳細はリンクからご確認ください。"

        circle = {
            "id":         start_id + i,
            "name":       c["name"],
            "university": "早稲田大学",
            "inkare":     False,
            "catchcopy":  catchcopy,
            "desc":       desc,
            "categories": ginfo["cats"],
            "intensity":  intensity,
            "vibe":       ginfo["vibe"],
            "size":       size,
            "cost":       cost,
            "vertical":   ginfo["vertical"],
            "activity":   "詳細はサイト参照",
            "members":    "詳細はサイト参照",
            "tags":       make_tags(c["genre_ja"], intensity, False, "早稲田大学"),
            "instagram":  sns_instagram or ("@" + c["name"].replace(" ","_").replace("　","_")[:20]),
            "photos":     [photo_key, f"smc_ws{c['id']}b/200/200", f"smc_ws{c['id']}c/200/200"],
            "scores":     ginfo["scores"],
            "waseda_id":  c["id"],
            "detail_url": c["detail_url"],
            "image_url":  img_url,
        }
        circles.append(circle)
    return circles

def convert_multi(raw_list, start_id=400):
    circles = []
    for i, c in enumerate(raw_list):
        gkey  = c.get("genre_key", "outdoor")
        ginfo = GENRE_MAP.get(gkey, GENRE_MAP["outdoor"])
        pr    = c.get("pr_text", "")
        name  = c["name"]
        univ  = c["university"]

        intensity = detect_intensity(pr, ginfo["intensity"])
        size      = detect_size(pr)
        cost      = detect_cost(pr)

        # 説明文
        desc = pr[:120] + "…" if pr and len(pr) > 120 else pr or name
        desc = re.split(r'[。\n]', desc)[0].strip()[:120]
        if not desc:
            desc = name

        # photoはpicsum fallback
        seed = f"smc_{c['id']}"
        photos = [f"{seed}/400/400", f"{seed}b/200/200", f"{seed}c/200/200"]

        circle = {
            "id":         start_id + i,
            "name":       name,
            "university": univ,
            "inkare":     False,
            "catchcopy":  c.get("catchcopy", name),
            "desc":       desc,
            "categories": ginfo["cats"],
            "intensity":  intensity,
            "vibe":       ginfo["vibe"],
            "size":       size,
            "cost":       cost,
            "vertical":   ginfo["vertical"],
            "activity":   "詳細はサイト参照",
            "members":    "詳細はサイト参照",
            "tags":       make_tags(c["genre_ja"], intensity, False, univ),
            "instagram":  "",
            "photos":     photos,
            "scores":     ginfo["scores"],
            "detail_url": c.get("detail_url", ""),
            "image_url":  "",
        }
        circles.append(circle)
    return circles


def main():
    # 早稲田データ
    waseda_circles = []
    if os.path.exists(SRC_WASEDA):
        with open(SRC_WASEDA, encoding="utf-8") as f:
            waseda_circles = convert_waseda(json.load(f), start_id=100)
        print(f"早稲田: {len(waseda_circles)}件")
    else:
        print(f"[WARNING] {SRC_WASEDA} が見つかりません")

    # 他大学データ (Webスクレイピング)
    multi_circles = []
    if os.path.exists(SRC_MULTI):
        with open(SRC_MULTI, encoding="utf-8") as f:
            multi_circles = convert_multi(json.load(f), start_id=400)
        print(f"他大学(Web): {len(multi_circles)}件")
    else:
        print(f"[WARNING] {SRC_MULTI} が見つかりません")

    # PDF大学データ (慶應・東大)
    pdf_circles = []
    if os.path.exists(SRC_PDF):
        with open(SRC_PDF, encoding="utf-8") as f:
            pdf_circles = convert_multi(json.load(f), start_id=2000)
        print(f"PDF大学(慶應・東大): {len(pdf_circles)}件")
    else:
        print(f"[WARNING] {SRC_PDF} が見つかりません")

    all_circles = waseda_circles + multi_circles + pdf_circles
    total = len(all_circles)

    # JS出力
    js  = "// 全大学公認サークルデータ（自動生成）\n"
    js += f"// 総件数: {total}件\n"
    js += "const ALL_CIRCLES = " + json.dumps(all_circles, ensure_ascii=False, indent=2) + ";\n"

    with open(DEST, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"\n✅ {DEST} に {total}件 出力完了")

    # サマリー
    univ_count = Counter(c["university"] for c in all_circles)
    print("\n--- 大学別件数 ---")
    for u, cnt in sorted(univ_count.items(), key=lambda x: -x[1]):
        print(f"  {u}: {cnt}件")

    cat_count = Counter(c["categories"][0] for c in all_circles)
    print("\n--- カテゴリ別件数 ---")
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}件")

if __name__ == "__main__":
    main()
