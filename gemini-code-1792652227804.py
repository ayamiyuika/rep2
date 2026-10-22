import streamlit as st
import pandas as pd
import urllib.request
import re
import datetime
import time

# ページ設定
st.set_page_config(
    page_title="都ホテルズ 楽天トラベル口コミ分析",
    page_icon="🏨",
    layout="wide"
)

# --- 1. 都ホテルズ 楽天トラベルID対応リスト ---
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

# 楽天トラベル収集関数（進捗コールバック対応）
def fetch_rakuten_reviews_with_progress(hotel_name, hotel_id, max_pages, progress_bar, status_text):
    reviews_data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for page in range(1, max_pages + 1):
        # 進行状況のテキストとバーを更新
        current_progress = (page - 1) / max_pages
        progress_bar.progress(current_progress)
        status_text.info(f"⏳ **[{page}/{max_pages} ページ目を巡回中...]** 楽天トラベルからデータを取得・解析しています（現在 {len(reviews_data)} 件抽出済）")

        url = f"https://travel.rakuten.co.jp/HOTEL/{hotel_id}/review.html" if page == 1 else f"https://travel.rakuten.co.jp/HOTEL/{hotel_id}/review_p{page}.html"
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('euc-jp', errors='ignore')

            boxes = re.findall(r'(<(?:div|dl)[^>]*class="[^"]*commentBox[^"]*"[\s\S]*?</(?:div|dl)>)', html)
            if not boxes:
                status_text.warning(f"ℹ️ {page}ページ目以降の口コミが見つからなかったため、収集を終了しました。")
                break

            for box in boxes:
                # 投稿日
                date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', box)
                post_date = datetime.date.today()
                if date_match:
                    y, m, d = date_match.groups()
                    post_date = datetime.date(int(y), int(m), int(d))

                # 宿泊年月
                stay_match = re.search(r'(\d{4}年\d{1,2}月)', box)
                stay_date_str = stay_match.group(1) if stay_match else "不明"

                # 評価
                rate_match = re.search(r'class="rate">[^0-9]*([0-9\.]+)', box)
                score = float(rate_match.group(1)) if rate_match else 3.0

                # 本文
                comment_match = re.search(r'class="comment"[^>]*>([\s\S]*?)</p>', box)
                if not comment_match:
                    continue
                body = re.sub(r'<br\s*/?>', '\n', comment_match.group(1))
                body = re.sub(r'<[^>]+>', '', body).strip()

                if not body:
                    continue

                cat, sentiment = analyze_review_text(body, score)
                reviews_data.append({
                    "ホテル名": hotel_name,
                    "サイト名": "楽天トラベル",
                    "投稿日": post_date,
                    "宿泊日": stay_date_str,
                    "評価": score,
                    "感情判定": sentiment,
                    "分類": cat,
                    "本文": body
                })

            time.sleep(1) # サーバー負荷防止のウェイト
        except Exception as e:
            status_text.error(f"⚠️ {page}ページ目の取得中にエラーが発生しました: {e}")
            break

    # 完了状態の更新
    progress_bar.progress(1.0)
    status_text.success(f"✅ 収集完了！ 合計 **{len(reviews_data)} 件** の口コミを取得・分析しました。")
    return pd.DataFrame(reviews_data)

# --- 2. サイドバーUI ---
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

# セッション状態の管理
if "current_df" not in st.session_state:
    st.session_state.current_df = pd.DataFrame()
if "loaded_hotel" not in st.session_state:
    st.session_state.loaded_hotel = ""

# --- 3. メイン画面 ---
st.title(f"【{selected_hotel}】 楽天トラベル口コミ分析")

# ボタンが押されたら進行状況UIを表示して処理開始
if fetch_button:
    st.markdown("### 📡 データ収集ステータス")
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    df_fetched = fetch_rakuten_reviews_with_progress(
        selected_hotel, 
        HOTEL_DICT[selected_hotel], 
        pages_to_fetch, 
        progress_bar, 
        status_text
    )
    st.session_state.current_df = df_fetched
    st.session_state.loaded_hotel = selected_hotel

df = st.session_state.current_df

if df.empty or st.session_state.loaded_hotel != selected_hotel:
    st.info("👈 左側のサイドバーにある **「楽天トラベルから口コミを収集」** ボタンを押すと収集が開始されます。")
else:
    s_date, e_date = date_range if len(date_range) == 2 else (date_range[0], datetime.date.today())
    filtered_df = df[(df["投稿日"] >= s_date) & (df["投稿日"] <= e_date)].sort_values(by="投稿日", ascending=False)

    if filtered_df.empty:
        st.warning("指定された期間内に該当する口コミがありませんでした。期間を変更してください。")
    else:
        avg_score = round(filtered_df["評価"].mean(), 2)
        total_count = len(filtered_df)
        pos_count = (filtered_df["感情判定"] == "ポジティブ").sum()
        pos_rate = round((pos_count / total_count) * 100, 1)

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("収集口コミ件数", f"{total_count} 件")
        c2.metric("平均評価スコア", f"{avg_score} / 5.0")
        c3.metric("高評価率", f"{pos_rate} %")

        all_cats = [c for sublist in filtered_df["分類"].str.split("、") for c in sublist if c != "全体・その他"]
        top_topic = pd.Series(all_cats).value_counts().index[0] if all_cats else "総合体験"

        with st.container(border=True):
            st.subheader("🤖 AI分析：全体の傾向とサマリー")
            st.markdown(f"""
            - **評価傾向**: 対象期間内の平均スコアは **{avg_score}点** で、**{pos_rate}%** がポジティブな評価です。
            - **最頻出カテゴリ**: **「{top_topic}」** に関する言及が最多です。
            """)

        st.markdown("---")
        st.subheader("📋 口コミ一覧（最新順・全件表示）")

        for _, row in filtered_df.iterrows():
            with st.container(border=True):
                h1, h2, h3, h4 = st.columns([2, 2, 2, 2])
                h1.markdown(f"🏨 **サイト**: {row['サイト名']}")
                h2.markdown(f"📅 **投稿日**: {row['投稿日']}")
                h3.markdown(f"🛏️ **宿泊年月**: {row['宿泊日']}")
                h4.markdown(f"⭐ **評価**: **{row['評価']}** / 5.0")
                st.markdown(f"🏷️ **分類**: `{row['分類']}`")
                st.info(row["本文"])
