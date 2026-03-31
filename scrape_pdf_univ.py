"""
PDF大学サークルデータ収集スクリプト
対象: 慶應義塾大学 (PDF), 東京大学 (PDF)
"""
import urllib.request, pdfplumber, io, json, re, os
from collections import Counter

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "pdf_univ_circles.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (research bot; contact: research@example.com)"}

GENRE_KEYWORDS = {
    "baseball":              ["野球", "ベースボール"],
    "football":              ["サッカー", "蹴球", "ラグビー", "アメリカンフットボール", "アメフト"],
    "futsal":                ["フットサル"],
    "basketball":            ["バスケ", "バスケットボール", "籠球"],
    "tennis":                ["テニス", "庭球", "ソフトテニス"],
    "volleyball":            ["バレー", "バレーボール", "排球"],
    "golf":                  ["ゴルフ"],
    "badminton":             ["バドミントン", "羽球"],
    "dance":                 ["ダンス", "チア", "社交ダンス", "ベリーダンス", "YOSAKOI", "ソーラン", "フラ", "ソングリーディング"],
    "martial-arts":          ["剣道", "柔道", "空手", "弓道", "合気道", "合氣道", "少林寺", "レスリング", "ボクシング",
                              "フェンシング", "アーチェリー", "洋弓", "なぎなた", "相撲", "躰道", "杖道", "居合",
                              "銃剣道", "棒術", "新体道", "拳法"],
    "skiing":                ["スキー", "スノーボード"],
    "swimming":              ["水泳", "水球", "競泳", "ダイビング", "シンクロ", "水上スキー"],
    "outdoor":               ["アウトドア", "登山", "ハイキング", "ワンダーフォーゲル", "ワンゲル",
                              "サイクリング", "キャンプ", "探検", "陸上", "マラソン", "駅伝",
                              "トライアスロン", "ラクロス", "ホッケー", "ボート", "カヌー", "ヨット",
                              "セーリング", "体操", "新体操", "ハンドボール", "ソフトボール", "アルティメット",
                              "自転車競技", "スケート", "アイスホッケー", "端艇", "馬術", "航空", "競走",
                              "山岳", "弓術", "器械体操", "重量挙"],
    "music":                 ["音楽", "バンド", "オーケストラ", "管弦楽", "アカペラ", "合唱", "吹奏楽",
                              "軽音", "ジャズ", "弦楽", "室内楽", "マンドリン", "フォーク", "ギター",
                              "ピアノ", "クラシック", "ロック", "和太鼓", "マーチング", "箏曲", "雅楽",
                              "ソサエティー", "SOUND", "MUSIC", "ORCHESTRA", "CHOIR", "JAZZ"],
    "theater":               ["演劇", "劇団", "ミュージカル", "落語", "漫才", "お笑い", "声優", "朗読",
                              "歌舞伎", "狂言", "能楽", "弁論"],
    "cinema":                ["映画", "映像", "シネマ", "フィルム", "動画", "放送"],
    "fine-art":              ["美術", "絵画", "写真", "陶芸", "デザイン", "漫画", "マンガ", "アニメ",
                              "イラスト", "書道", "工芸", "版画", "彫刻", "造形", "アート", "折り紙",
                              "CG", "華道", "茶道", "茶華道", "かるた", "奇術", "模型", "盆栽",
                              "郷土", "囲碁", "将棋"],
    "international-exchange":["国際", "交流", "ESS", "外国語", "多文化", "海外", "留学",
                              "インターナショナル", "グローバル", "フェアトレード", "手話",
                              "INTERNATIONAL", "GLOBAL"],
    "volunteer":             ["ボランティア", "社会貢献", "福祉", "NPO", "環境保全", "地域貢献", "赤十字",
                              "支援", "SDGs", "福祉"],
    "technology":            ["プログラミング", "IT", "コンピュータ", "ロボット", "AI", "情報処理",
                              "エンジニア", "電子工学", "天文", "物理", "化学", "数学",
                              "統計", "電気", "機械", "航空宇宙", "計算", "電算", "無線", "サイエンス",
                              "ROBO", "Tech", "科学", "工学", "人工衛星", "ロケット", "宇宙"],
    "economy":               ["経済", "ビジネス", "起業", "投資", "経営", "MBA", "コンサル",
                              "簿記", "会計", "金融", "政策", "法律", "ディベート", "模擬国連",
                              "政治", "クイズ", "広告", "証券", "法学", "研究会", "国際法"],
    "language":              ["語学", "スペイン語", "フランス語", "中国語", "韓国語", "ドイツ語",
                              "イタリア語", "ロシア語", "英語研究", "英米", "ラテン"],
}

GENRES_JA = {
    "baseball": "野球", "football": "サッカー・ラグビー", "futsal": "フットサル",
    "basketball": "バスケットボール", "tennis": "テニス", "volleyball": "バレーボール",
    "golf": "ゴルフ", "badminton": "バドミントン", "dance": "ダンス",
    "martial-arts": "武道", "skiing": "スキー・スノボ", "swimming": "水泳",
    "outdoor": "アウトドア・スポーツ", "music": "音楽", "theater": "演劇",
    "cinema": "映画・映像", "fine-art": "美術・アート", "international-exchange": "国際交流",
    "volunteer": "ボランティア", "technology": "テクノロジー", "economy": "経済・ビジネス",
    "language": "語学",
}

# 東大の活動分野 → ジャンルキー マッピング
TODAI_FIELD_MAP = {
    "音楽・合唱":   "music",
    "芸術・文化":   "fine-art",
    "学術・科学":   "technology",
    "体育・スポーツ": "outdoor",
    "趣味・交流":   "international-exchange",
    "社会・福祉":   "volunteer",
    "報道・出版":   "cinema",
    "自然・環境":   "outdoor",
    "宗教":        "fine-art",
    "留学生":      "international-exchange",
    "その他":      "outdoor",
}

def detect_genre(name, desc="", field=""):
    # 東大の活動分野があればそれを優先して補助
    base = TODAI_FIELD_MAP.get(field, None)
    text = name + " " + (desc or "")
    for genre, keywords in GENRE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return genre
    return base or "outdoor"

def is_valid_name(name):
    if not name or len(name) < 2 or len(name) > 60:
        return False
    if re.match(r'^[\d\s\-\./・]+$', name):
        return False
    # ヘッダー行
    if name in {"所属", "分類", "団体名", "No.", "略称", "設立年", "活動分野", "活動概要"}:
        return False
    return True

def make_circle(uid, univ_name, name, detail_url="", pr_text="", field=""):
    name = name.strip()
    if not name or len(name) < 2:
        return None
    genre_key = detect_genre(name, pr_text, field)
    return {
        "id": str(uid),
        "name": name,
        "catchcopy": name,
        "genre_key": genre_key,
        "genre_ja": GENRES_JA[genre_key],
        "university": univ_name,
        "detail_url": detail_url,
        "image_url": "",
        "sns_links": {},
        "pr_text": pr_text.strip() if pr_text else "",
    }

def fetch_pdf(url):
    """URLからPDFをダウンロードしてバイト列を返す"""
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=30).read()


# ===== 慶應義塾大学 =====
def fetch_keio():
    circles = []
    seen = set()
    url = "https://www.keio.ac.jp/en/student-life/files/athletics-recreation/Official_Student_Groups.pdf"
    # 除外する行（全塾協議会中央機関など運営団体は含めない）
    KEIO_SKIP = {
        "所属", "分類", "団体名", "全塾協議会本部", "全塾協議会",
        "体育会本部", "文化団体連盟本部", "慶應義塾大学 学生総合センター",
    }
    try:
        print("  PDFダウンロード中...")
        data = fetch_pdf(url)
        print(f"  {len(data)} bytes")
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            print(f"  ページ数: {len(pdf.pages)}")
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 3:
                            continue
                        affiliation = (row[0] or "").strip()
                        name = (row[2] or "").strip()
                        # ヘッダー行スキップ
                        if name in KEIO_SKIP or affiliation in KEIO_SKIP:
                            continue
                        if not is_valid_name(name):
                            continue
                        # 改行を含む場合は最初の行を使用
                        name = name.split("\n")[0].strip()
                        if name not in seen and is_valid_name(name):
                            seen.add(name)
                            circles.append(make_circle(
                                f"keio_{len(circles)}", "慶應義塾大学", name
                            ))
    except Exception as e:
        print(f"  [ERROR] 慶應義塾大学: {e}")
    return [c for c in circles if c]


# ===== 東京大学 =====
def fetch_todai():
    circles = []
    seen = set()
    url = "https://www.u-tokyo.ac.jp/content/400281560.pdf"
    TODAI_SKIP = {
        "No.", "団体名", "（略称）", "設立年", "活動分野",
    }
    # 「東京大学」プレフィックスを除去する
    TODAI_PREFIX = "東京大学"
    try:
        print("  PDFダウンロード中...")
        data = fetch_pdf(url)
        print(f"  {len(data)} bytes")
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            print(f"  ページ数: {len(pdf.pages)}")
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 5:
                            continue
                        raw_name = (row[1] or "").strip()
                        field    = (row[4] or "").strip()
                        desc     = (row[5] or "").strip() if len(row) > 5 else ""
                        website  = (row[9] or "").strip() if len(row) > 9 else ""

                        # 改行で複数行になっている場合は最初の行
                        raw_name = raw_name.split("\n")[0].strip()
                        desc     = desc.split("\n")[0].strip()

                        # スキップ
                        if raw_name in TODAI_SKIP:
                            continue

                        # 「東京大学〇〇」→「〇〇」に正規化
                        name = raw_name
                        if name.startswith(TODAI_PREFIX):
                            name = name[len(TODAI_PREFIX):].strip()

                        # スラッシュで英語表記が続く場合は日本語部分のみ
                        if "/" in name:
                            name = name.split("/")[0].strip()

                        if not is_valid_name(name):
                            continue
                        if name not in seen:
                            seen.add(name)
                            circles.append(make_circle(
                                f"todai_{len(circles)}", "東京大学", name,
                                detail_url=website if website and website != "ー" else "",
                                pr_text=desc if desc and desc != "ー" else "",
                                field=field,
                            ))
    except Exception as e:
        print(f"  [ERROR] 東京大学: {e}")
    return [c for c in circles if c]


def main():
    all_circles = []
    scrapers = [
        ("慶應義塾大学", fetch_keio),
        ("東京大学",     fetch_todai),
    ]

    print("=== PDF大学サークルデータ収集 ===\n")
    for univ_name, fn in scrapers:
        print(f"取得中: {univ_name}")
        circles = fn()
        print(f"  → {len(circles)}件")
        for c in circles[:5]:
            print(f"    例: {c['name']} ({c['genre_key']})")
        all_circles.extend(circles)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_circles, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {len(all_circles)}件 → {OUTPUT_PATH}")
    print("\n--- 大学別件数 ---")
    for u, cnt in sorted(Counter(c["university"] for c in all_circles).items(), key=lambda x: -x[1]):
        print(f"  {u}: {cnt}件")


if __name__ == "__main__":
    main()
