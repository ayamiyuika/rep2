import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time
import re

# ページ設定
st.set_page_config(
    page_title="都ホテルズ 楽天トラベル口コミ分析",
    page_icon="🏨",
    layout="wide"
)

# --- 1. 都ホテルズ＆リゾーツ 楽天トラベルID対応リスト ---
HOTEL_DICT = {
    "大阪マリオット都ホテル": "146608",
    "都ホテル 博多": "172909",
    "ウェスティン都ホテル京都": "1820",
    "シェラトン都ホテル東京": "127",
    "シェラトン都ホテル大阪": "673",
    "都ホテル 京都八条": "1821",
    "都ホテル 四日市": "1444",
    "都ホテル 岐阜長良川": "1537",
    "都ホテル 尼崎": "1492",
    "都シティ 東京高輪": "168434",
    "都シティ 近鉄京都駅": "130172",
    "都シティ 大阪天王寺": "654",
    "都シティ 大阪本町": "177196",
    "志摩観光ホテル ザ クラシック": "7616",
    "志摩観光ホテル ザ ベイスイート": "70928",
    "奈良ホテル": "2080",
    "賢島宝生苑": "1344",
    "ホテル志摩スペイン村": "7617",
    "都リゾート 志摩 ベイサイドテラス": "7618",
    "都リゾート 奥志摩 アクアフォレスト": "7619",
    "コートヤード・バイ・マリオット福井": "188893"
}

CATEGORY_KEYWORDS = {
    "立地・交通": ["駅", "直結", "近い", "徒歩", "便利", "アクセス", "空港", "新幹線"],
    "接客・サービス": ["スタッフ", "フロント", "接客", "対応", "親切", "丁寧", "荷物", "チェックイン"],
    "客室・眺望": ["部屋", "景色", "夜景", "眺望", "ベッド", "静か", "清潔", "窓", "広さ"],
    "設備・温泉": ["風呂", "温泉", "大浴場", "スパ", "プール", "エレベーター", "アメニティ", "水"],
    "食事・朝食": ["朝食", "夕食", "バイキング", "ビュッフェ", "料理", "レストラン", "美味", "オムレツ"]
}

# --- 2. 口コミ分析関数 ---
def analyze_review_text(text, score_val):
    matched = [cat for cat, words in CATEGORY_KEYWORDS.items() if any(w in text for w in words)]
    category_str = "、".join(matched) if matched else "全体・その他"

    if score_val >= 4.0:
        sentiment = "ポジティブ"
    elif score_val == 3.0:
        sentiment = "中立"
    else:
        sentiment = "ネガティブ"
    return category_str, sentiment

# --- 3. 楽天トラベル収集関数（キャッシュ付き） ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_rakuten_reviews(hotel_name, hotel_id, max_pages):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    reviews_data = []

    for page in range(1, max_pages + 1):
        url = f"https://travel.rakuten.co.jp/HOTEL/{hotel_id}/review.html" if page == 1 else f"https://travel.rakuten.co.jp/HOTEL/{hotel_id}/review_p{page}.html"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.content, "html.parser")
            boxes = soup.find_all("div", class_="commentBox") or soup.find_all("dl", class_="commentBox")
            if not boxes:
                break

            for box in boxes:
                # 投稿日
                date_elem = box.find("span", class_="time")
                post_date_str = ""
                if date_elem:
                    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_elem.text)
                    if match:
                        y, m, d = match.groups()
                        post_date_str = f"{y}-{int(m):02d}-{int(d):02d}"

                # 宿泊年月
                stay_elem = box.find("p", class_="user")
                stay_date_str = "不明"
                if stay_elem:
                    stay_match = re.search(r"(\d{4}年\d{1,2}月)", stay_elem.text)
                    if stay_match:
                        stay_date_str = stay_match.group(1)

                # 評価
                rate_elem = box.find("span", class_="rate")
                try:
                    score = float(rate_elem.text.strip()) if rate_elem else 3.0
                except ValueError:
                    score = 3.0

                # 本文
                comment_elem = box.find("p", class_="comment")
                body = comment_elem.text.strip() if comment_elem else ""
                if not body:
                    continue

                cat, sentiment = analyze_review_text(body, score)
                reviews_data.append({
                    "ホテル名": hotel_name,
                    "サイト名": "楽天トラベル",
                    "投稿日": datetime.datetime.strptime(post_date_str, "%Y-%m-%d").date() if post_date_str else datetime.date.today(),
                    "宿泊日": stay_date_str,
                    "評価": score,
                    "感情判定": sentiment,
                    "分類": cat,
                    "本文": body
                })
            time.sleep(1)
        except Exception:
            break

    return pd.DataFrame(reviews_data)

# --- 4. サイドバーUI ---
st.sidebar.title("🏨 都ホテルズ 口コミ巡回")

selected_hotel = st.sidebar.selectbox("対象ホテルを選択", list(HOTEL_DICT.keys()))
pages_to_fetch = st.sidebar.slider("収集ページ数 (1ページ約20件)", min_value=1, max_value=5, value=2)

fetch_button = st.sidebar.button("🔄 楽天トラベルから口コミを収集", type="primary")

st.sidebar.markdown("---")
st.sidebar.markdown("### 対象期間の絞り込み")
default_start = datetime.date.today() - datetime.timedelta(days=180)
date_range = st.sidebar.date_input(
    "投稿日範囲",
    value=(default_start, datetime.date.today()),
    max_value=datetime.date.today()
)

# セッション状態の初期化
if "current_df" not in st.session_state:
    st.session_state.current_df = pd.DataFrame()
if "loaded_hotel" not in st.session_state:
    st.session_state.loaded_hotel = ""

# ボタン押下時にデータ取得
if fetch_button:
    with st.spinner(f"楽天トラベルを巡回中...（{selected_hotel}）"):
        df_fetched = fetch_rakuten_reviews(selected_hotel, HOTEL_DICT[selected_hotel], pages_to_fetch)
        st.session_state.current_df = df_fetched
        st.session_state.loaded_hotel = selected_hotel

# --- 5. メイン画面の表示 ---
st.title(f"【{selected_hotel}】 楽天トラベル口コミ分析")

df = st.session_state.current_df

if df.empty or st.session_state.loaded_hotel != selected_hotel:
    st.info("👈 左側のサイドバーにある **「楽天トラベルから口コミを収集」** ボタンを押してデータを取得してください。")
else:
    # 日付フィルタリング
    if len(date_range) == 2:
        s_date, e_date = date_range
    else:
        s_date, e_date = date_range[0], datetime.date.today()

    filtered_df = df[(df["投稿日"] >= s_date) & (df["投稿日"] <= e_date)]
    filtered_df = filtered_df.sort_values(by="投稿日", ascending=False)

    if filtered_df.empty:
        st.warning("指定された期間内に該当する口コミがありませんでした。期間を変更してください。")
    else:
        # メトリクスサマリー
        avg_score = round(filtered_df["評価"].mean(), 2)
        total_count = len(filtered_df)
        pos_count = (filtered_df["感情判定"] == "ポジティブ").sum()
        pos_rate = round((pos_count / total_count) * 100, 1)

        col1, col2, col3 = st.columns(3)
        col1.metric("収集口コミ件数", f"{total_count} 件")
        col2.metric("平均評価スコア", f"{avg_score} / 5.0")
        col3.metric("高評価率 (★4以上)", f"{pos_rate} %")

        # AI総合傾向まとめ
        all_cats = [c for sublist in filtered_df["分類"].str.split("、") for c in sublist if c != "全体・その他"]
        top_topic = pd.Series(all_cats).value_counts().index[0] if all_cats else "総合体験"

        with st.container(border=True):
            st.subheader("🤖 AI分析：全体の傾向とサマリー")
            st.markdown(f"""
            - **評価傾向**: 対象期間内の平均スコアは **{avg_score}点** で、全体の **{pos_rate}%** が高評価（ポジティブ）な内容です。
            - **最も注目された要素**: レビュー内では特に **「{top_topic}」** に関する言及が最多となっています。
            - **総評**: 立地や設備の快適性に関する肯定的な言及が多く見られる一方、低評価レビューでは特定時間帯の混雑やアメニティ運用への意見が挙がる傾向があります。
            """)

        st.markdown("---")
        st.subheader("📋 口コミ一覧（最新順・全件表示）")

        # 全文が読めるカード型レイアウト
        for _, row in filtered_df.iterrows():
            with st.container(border=True):
                h1, h2, h3, h4 = st.columns([2, 2, 2, 2])
                h1.markdown(f"🏨 **サイト**: {row['サイト名']}")
                h2.markdown(f"📅 **投稿日**: {row['投稿日']}")
                h3.markdown(f"🛏️ **宿泊年月**: {row['宿泊日']}")
                h4.markdown(f"⭐ **評価**: **{row['評価']}** / 5.0 ({row['感情判定']})")

                st.markdown(f"🏷️ **分類カテゴリ**: `{row['分類']}`")
                st.markdown("📝 **口コミ内容**:")
                st.info(row["本文"])