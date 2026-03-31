"""
多大学サークルデータ収集スクリプト v2
対象: 法政・東京理科・一橋・明治・立教・青山・中央・上智
"""
import requests, json, time, os, re
from bs4 import BeautifulSoup
from collections import Counter

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "multi_univ_circles.json")
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
    "martial-arts":          ["剣道", "柔道", "空手", "弓道", "合気道", "少林寺", "レスリング", "ボクシング",
                              "フェンシング", "アーチェリー", "洋弓", "なぎなた", "相撲", "躰道", "杖道", "居合",
                              "銃剣道", "棒術", "新体道"],
    "skiing":                ["スキー", "スノーボード"],
    "swimming":              ["水泳", "水球", "競泳", "ダイビング", "シンクロ", "水上スキー"],
    "outdoor":               ["アウトドア", "登山", "ハイキング", "ワンダーフォーゲル", "ワンゲル",
                              "サイクリング", "キャンプ", "探検", "陸上", "マラソン", "駅伝",
                              "トライアスロン", "ラクロス", "ホッケー", "ボート", "カヌー", "ヨット",
                              "セーリング", "体操", "新体操", "ハンドボール", "ソフトボール", "アルティメット",
                              "自転車競技", "スケート", "アイスホッケー"],
    "music":                 ["音楽", "バンド", "オーケストラ", "管弦楽", "アカペラ", "合唱", "吹奏楽",
                              "軽音", "ジャズ", "弦楽", "室内楽", "マンドリン", "フォーク", "ギター",
                              "ピアノ", "クラシック", "ロック", "和太鼓", "マーチング"],
    "theater":               ["演劇", "劇団", "ミュージカル", "落語", "漫才", "お笑い", "声優", "朗読", "歌舞伎"],
    "cinema":                ["映画", "映像", "シネマ", "フィルム", "動画"],
    "fine-art":              ["美術", "絵画", "写真", "陶芸", "デザイン", "漫画", "マンガ", "アニメ",
                              "イラスト", "書道", "工芸", "版画", "彫刻", "造形", "アート", "折り紙",
                              "CG", "華道", "茶道", "茶華道"],
    "international-exchange":["国際", "交流", "ESS", "外国語", "多文化", "海外", "留学",
                              "インターナショナル", "グローバル", "フェアトレード", "手話"],
    "volunteer":             ["ボランティア", "社会貢献", "福祉", "NPO", "環境保全", "地域貢献", "赤十字"],
    "technology":            ["プログラミング", "IT", "コンピュータ", "ロボット", "AI", "情報処理",
                              "エンジニア", "電子工学", "天文", "物理", "化学", "数学",
                              "統計", "電気", "機械", "航空", "計算", "電算", "無線", "サイエンス"],
    "economy":               ["経済", "ビジネス", "起業", "投資", "経営", "MBA", "コンサル",
                              "簿記", "会計", "金融", "政策", "法律", "ディベート", "模擬国連",
                              "政治", "将棋", "囲碁", "クイズ", "広告", "証券", "法学"],
    "language":              ["語学", "スペイン語", "フランス語", "中国語", "韓国語", "ドイツ語",
                              "イタリア語", "ロシア語", "英語研究", "英米"],
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

# 明確にナビゲーション項目と分かるキーワード
NAV_EXACT = {
    "HOME", "MENU", "ホーム", "トップ", "サイトマップ", "プライバシーポリシー",
    "お問い合わせ", "アクセス", "寄付", "採用情報", "資料請求", "Language",
    "English", "검색", "SEARCH", "Page top", "ページトップ",
}
NAV_CONTAINS = [
    "学部", "研究科", "センター", "図書館", "大学院", "付属", "事務局",
    "キャンパス案内", "入試", "入学", "受験", "カリキュラム", "シラバス",
    "就職", "留学プログラム", "奨学金", "学費", "履修", "証明書",
    "Copyright", "All Rights Reserved",
]

def detect_genre(name, desc=""):
    text = name + " " + (desc or "")
    for genre, keywords in GENRE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return genre
    return "outdoor"

def make_circle(uid, univ_name, name, detail_url="", pr_text=""):
    name = name.strip()
    if not name or len(name) < 2:
        return None
    genre_key = detect_genre(name, pr_text)
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

def is_valid_name(name):
    name = name.strip()
    if not name or len(name) < 2 or len(name) > 45:
        return False
    if name in NAV_EXACT:
        return False
    for kw in NAV_CONTAINS:
        if kw in name:
            return False
    # 数字のみ・記号のみ
    if re.match(r'^[\d\s\-\./・]+$', name):
        return False
    return True


# ===== 法政大学 =====
def fetch_hosei():
    url = "https://www.hosei.ac.jp/campuslife/club/toroku/"
    circles = []
    seen = set()
    HOSEI_SKIP = {
        "市ケ谷キャンパス", "多摩キャンパス", "小金井キャンパス",
        "体育会", "学術団体", "学生団体", "こちら", "詳細はこちらからご確認ください。",
    }
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        # .box-cmn.editor クラスのdivにサークル名が格納されている
        for div in soup.find_all("div", class_="editor"):
            text = div.get_text(separator="\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for line in lines:
                if line in HOSEI_SKIP:
                    continue
                # 説明文（長い文や「〜はこちら」「〜ください」を除外）
                if len(line) > 50:
                    continue
                if any(kw in line for kw in ["はこちら", "ください", "手続き", "システム", "登録団体", "GCSS", "※"]):
                    continue
                if is_valid_name(line) and line not in seen:
                    seen.add(line)
                    circles.append(make_circle(f"hosei_{len(circles)}", "法政大学", line))
    except Exception as e:
        print(f"  [ERROR] 法政大学: {e}")
    return [c for c in circles if c]


# ===== 東京理科大学 =====
def fetch_tus():
    circles = []
    seen = set()
    for cat in [1, 2, 3]:
        url = f"https://www.tus-act.tus.ac.jp/club_circle/club_circle.php?category={cat}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(separator="\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if line == "READ MORE" and i > 0:
                    name = lines[i - 1].strip()
                    if is_valid_name(name) and name not in seen:
                        seen.add(name)
                        circles.append(make_circle(f"tus_{len(circles)}", "東京理科大学", name))
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERROR] 東京理科大学 category={cat}: {e}")
    return [c for c in circles if c]


# ===== 一橋大学 =====
def fetch_hitotsubashi():
    circles = []
    seen = set()
    urls = [
        "https://www.hit-u.ac.jp/shien/campuslife/circle/doukoukai.html",
        "https://www.hit-u.ac.jp/shien/campuslife/circle/taiikukai.html",
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.encoding = res.apparent_encoding  # エンコーディング修正
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(separator="\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if "学生代表者" in line and i > 0:
                    name = lines[i - 1].strip()
                    if "学生代表者" in name:
                        name = name.split("学生代表者")[0].strip()
                    if is_valid_name(name) and name not in seen:
                        seen.add(name)
                        pr = " ".join(lines[i:i + 3]) if i + 3 < len(lines) else ""
                        circles.append(make_circle(f"hitu_{len(circles)}", "一橋大学", name, pr_text=pr))
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERROR] 一橋大学 {url}: {e}")
    return [c for c in circles if c]


# ===== 明治大学 =====
def fetch_meiji():
    circles = []
    seen = set()
    sub_urls = [
        "http://www.meiji.ac.jp/campus/circle/og.html",        # 音楽・芸術
        "http://www.meiji.ac.jp/campus/circle/jg.html",        # 人文・社会
        "http://www.meiji.ac.jp/campus/circle/rg.html",        # レクリエーション・スポーツ
        "http://www.meiji.ac.jp/campus/circle/doukoukai_bun.html",  # 同好会(文化)
        "http://www.meiji.ac.jp/campus/circle/doukoukai_sp.html",   # 同好会(スポーツ)
        "http://www.meiji.ac.jp/campus/circle/rikaren.html",    # 理科部連合会
    ]
    MEIJI_NAV = {
        "サークル活動", "一覧へ", "ホーム", "公認サークル一覧", "理科部連合会（理科連）",
        "体育同好会連合会（体同連）", "音楽・芸術グループ", "人文・社会グループ",
        "レクリエーション・スポーツグループ", "同好会（文化系）", "同好会（スポーツ系）",
        "音楽", "芸術", "芸能", "体育", "スポーツ", "文化", "人文", "社会", "レクリエーション",
    }
    for url in sub_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(separator="\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            # h2タグを見つけてそれ以降の行からサークル名を取得
            # （明治のページはナビが最初にあり、h2以降がコンテンツ）
            h2 = soup.find("h2")
            if h2:
                start_text = h2.get_text(strip=True)
                start_idx = None
                for i, l in enumerate(lines):
                    if l == start_text:
                        start_idx = i
                        break
                if start_idx is not None:
                    lines = lines[start_idx + 1:]

            for line in lines:
                name = line.strip()
                # 「：」で終わるカテゴリ名を除外
                if name.endswith("：") or name.endswith(":"):
                    continue
                # スラッシュのみや記号のみを除外
                if re.match(r'^[/・\-\s]+$', name):
                    continue
                if name in MEIJI_NAV:
                    continue
                if is_valid_name(name) and name not in seen:
                    seen.add(name)
                    circles.append(make_circle(f"meiji_{len(circles)}", "明治大学", name))
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERROR] 明治大学 {url}: {e}")
    return [c for c in circles if c][:300]


# ===== 立教大学 =====
def fetch_rikkyo():
    url = "https://www.rikkyo.ac.jp/campuslife/support/extracurricular_activities/club_activities.html"
    circles = []
    seen = set()
    RIKKYO_SKIP = {
        "体育会の主な実績", "団体紹介", "関連リンク", "体育会", "学生キリスト教団体",
        "学生健康保険互助組合", "池袋キャンパス登録団体", "新座キャンパス登録団体",
        "その他の団体", "文化系", "スポーツ系",
    }
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        main = soup.find("main") or soup

        # aタグからサークルページへのリンクを取得
        for a in main.find_all("a", href=True):
            href = a.get("href", "")
            name = a.get_text(strip=True)
            # 立教サークルのURLパターン: /campuslife/support/extracurricular_activities/
            if (("extracurricular" in href or "club" in href or "circle" in href or "sport" in href)
                    and is_valid_name(name) and name not in seen and name not in RIKKYO_SKIP):
                seen.add(name)
                full_url = href if href.startswith("http") else "https://www.rikkyo.ac.jp" + href
                circles.append(make_circle(f"rikkyo_{len(circles)}", "立教大学", name, full_url))

        # フォールバック: テキストリストから取得（実績リストにサークル名が含まれる）
        if len(circles) < 20:
            text = main.get_text(separator="\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            # 「団体紹介」以降から、「〜部」「〜会」「〜クラブ」などのサークル名を取得
            in_content = False
            for line in lines:
                if line == "団体紹介":
                    in_content = True
                    continue
                if not in_content:
                    continue
                if line in RIKKYO_SKIP:
                    continue
                # サークル名らしい接尾語を持つもの
                if (is_valid_name(line) and line not in seen and
                        any(line.endswith(s) for s in
                            ["部", "会", "団", "クラブ", "サークル", "研究会", "同好会",
                             "愛好会", "連合", "委員会", "組合"])):
                    seen.add(line)
                    circles.append(make_circle(f"rikkyo_{len(circles)}", "立教大学", line))
    except Exception as e:
        print(f"  [ERROR] 立教大学: {e}")
    return [c for c in circles if c][:200]


# ===== 青山学院大学 =====
def fetch_aoyama():
    circles = []
    seen = set()
    urls = [
        "https://www.aoyama.ac.jp/life/activity/club/culture/",
        "https://www.aoyama.ac.jp/life/activity/club/sports/",
        "https://www.aoyama.ac.jp/life/activity/club/sagamihara/",
    ]
    AOYAMA_SKIP = {
        "青山連合会", "学生生活", "クラブ・課外活動", "クラブ・サークル", "学友会について",
        "部会（クラブ）", "文化系", "スポーツ系",
    }
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            main = soup.find("main") or soup
            text = main.get_text(separator="\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            # 「クラブ・サークル」や「部会」のキーワード以降からサークル名を取得
            in_content = False
            for line in lines:
                if "クラブ・サークル" in line or "部会（クラブ）" in line:
                    in_content = True
                    continue
                if not in_content:
                    continue
                if line in AOYAMA_SKIP:
                    continue
                if (is_valid_name(line) and line not in seen):
                    seen.add(line)
                    circles.append(make_circle(f"aoyama_{len(circles)}", "青山学院大学", line))
            time.sleep(0.5)
        except Exception as e:
            print(f"  [ERROR] 青山学院大学 {url}: {e}")
    return [c for c in circles if c][:200]


# ===== 中央大学 =====
def fetch_chuo():
    url = "https://www.chuo-u.ac.jp/connect/campus_life/activity.html"
    circles = []
    seen = set()
    CHUO_SECTION_HEADERS = {
        "体育連盟", "体育同好会連盟", "理工連盟", "準公認部会",
        "学術連盟", "文化連盟", "学芸連盟", "学友連盟", "Athletic", "Academic",
        "スポーツ系部活動･サークル一覧", "文化系部活動･サークル一覧",
    }
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        in_circle_section = False
        for line in lines:
            # サークル一覧セクションの開始を検出
            if "スポーツ系部活動" in line or "文化系部活動" in line:
                in_circle_section = True
                continue
            # セクション見出しをスキップ（でも開始トリガーとして使う）
            if line in CHUO_SECTION_HEADERS:
                continue
            if not in_circle_section:
                continue
            # カンマ区切りのサークル名リストを分割
            if "、" in line:
                parts = re.split(r"[、，]", line)
                for part in parts:
                    name = part.strip()
                    # 括弧内を除去
                    name = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
                    if is_valid_name(name) and name not in seen and len(name) >= 3:
                        seen.add(name)
                        circles.append(make_circle(f"chuo_{len(circles)}", "中央大学", name))
            else:
                # 単独行のサークル名（接尾語チェック）
                name = line.strip()
                if is_valid_name(name) and name not in seen:
                    if any(name.endswith(s) for s in
                           ["部", "会", "団", "クラブ", "サークル", "研究会", "同好会",
                            "倶楽部", "愛好会"]):
                        seen.add(name)
                        circles.append(make_circle(f"chuo_{len(circles)}", "中央大学", name))
    except Exception as e:
        print(f"  [ERROR] 中央大学: {e}")
    return [c for c in circles if c][:300]


# ===== 上智大学 =====
def fetch_sophia():
    # findsophia.jp の団体一覧を使用
    # ページ構造: サークル名 → 説明文 → 活動時間 → 場所 → 団体No.(6桁) → 所属組織 → 次のサークル名 ...
    url = "https://findsophia.jp/club-list/"
    circles = []
    seen = set()
    ORG_NAMES = {
        "体育団体連合会", "文化団体連合会", "音楽協議会", "演劇協議会", "同好会愛好会連合", "その他",
    }
    SOPHIA_NAV = {
        "FIND SOPHIA", "CLUB LIST", "上智大学サイト", "JP", "EN", "SOPHIANS' GUIDE",
        "VIDEOS", "LINKS", "利用規約", "Search", "課外活動団体一覧",
    }
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # 所属組織名の次の行がサークル名
        for i, line in enumerate(lines):
            if line in ORG_NAMES and i + 1 < len(lines):
                name = lines[i + 1].strip()
                if (is_valid_name(name) and name not in seen and
                        name not in SOPHIA_NAV and
                        not re.match(r'^\d{6}$', name) and
                        not name.endswith("です。") and
                        not name.endswith("ます。") and
                        not name.endswith("ください。")):
                    seen.add(name)
                    pr = lines[i + 2].strip() if i + 2 < len(lines) else ""
                    if len(pr) > 5 and len(pr) < 100:
                        circles.append(make_circle(f"sophia_{len(circles)}", "上智大学", name, pr_text=pr))
                    else:
                        circles.append(make_circle(f"sophia_{len(circles)}", "上智大学", name))
    except Exception as e:
        print(f"  [ERROR] 上智大学: {e}")
    return [c for c in circles if c][:200]


def main():
    all_circles = []
    scrapers = [
        ("法政大学",     fetch_hosei),
        ("東京理科大学", fetch_tus),
        ("一橋大学",     fetch_hitotsubashi),
        ("明治大学",     fetch_meiji),
        ("立教大学",     fetch_rikkyo),
        ("青山学院大学", fetch_aoyama),
        ("中央大学",     fetch_chuo),
        ("上智大学",     fetch_sophia),
    ]

    print("=== 多大学サークルデータ収集 v2 ===\n")
    for univ_name, fn in scrapers:
        print(f"取得中: {univ_name}")
        circles = fn()
        print(f"  → {len(circles)}件")
        for c in circles[:3]:
            print(f"    例: {c['name']} ({c['genre_key']})")
        all_circles.extend(circles)
        time.sleep(1.0)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_circles, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {len(all_circles)}件 → {OUTPUT_PATH}")
    print("\n--- 大学別件数 ---")
    for u, cnt in sorted(Counter(c["university"] for c in all_circles).items(), key=lambda x: -x[1]):
        print(f"  {u}: {cnt}件")

if __name__ == "__main__":
    main()
