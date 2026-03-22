import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import sys
import os
import time

# =========================================================
# ★ 金庫（Secrets）から鍵を取り出す
# =========================================================
CI_ID = os.getenv("CI_ID")
CI_PASS = os.getenv("CI_PASS")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# =========================================================
# ★ 監視リスト（ここに監視したいURLをすべて入れます）
# =========================================================
TARGET_LIST = [
    "https://www.ci-medical.com/dental/catalog_item/801Y202",
    "https://www.ci-medical.com/dental/catalog_item/801Y201",
    "https://www.ci-medical.com/dental/catalog_item/801Y191",
    "https://www.ci-medical.com/dental/catalog_item/801Y10156",
    "https://www.ci-medical.com/dental/catalog_item/801Y173",
    "https://www.ci-medical.com/dental/catalog_item/801Y458"
]

def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    })

    print("ログイン処理を開始します...")
    try:
        # Ciメディカルのログインページ
        login_url = "https://www.ci-medical.com/login" 
        res = session.get(login_url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # ページ内の隠し鍵（tokenなど）をすべて自動回収
        login_data = {}
        for input_tag in soup.find_all("input"):
            if input_tag.has_attr("name"):
                login_data[input_tag["name"]] = input_tag.get("value", "")

        # 金庫から取り出したIDとパスワードをセット
        login_data["login_id"] = CI_ID      
        login_data["password"] = CI_PASS

        # ログイン実行
        session.post(login_url, data=login_data, timeout=10)
        print("ログイン通信完了")
        time.sleep(2)

    except Exception as e:
        print(f"ログイン処理でエラー: {e}")
        sys.exit(1)

    found_items = [] # 復活した商品を貯めておくリスト

    print("在庫チェックを開始します...")
    
    # 監視リストを順番にチェックしていく
    for url in TARGET_LIST:
        print(f"チェック中: {url}")
        try:
            r = session.get(url, timeout=10)
            r.encoding = r.apparent_encoding

            # ★作戦：「買い物カゴに入れる」ボタンが出現したかを探す！
            if "買い物カゴに入れる" in r.text:
                if "Ci" in r.text: # 別ページに飛ばされていないかの安全チェック
                    print(" 〇 変化あり（在庫復活の可能性！）")
                    found_items.append(f"・{url}")
                else:
                    print(" × ログイン失敗か別ページに飛ばされています")
            else:
                print(" × 在庫なし、またはログイン画面に弾かれています")
        except Exception as e:
            print(f" 取得失敗: {e}")
        
        time.sleep(2) # 連続アクセスで目をつけられないように2秒休憩

    # 1つでも復活した商品があればメールを飛ばす
    if found_items:
        send_email(found_items)
    else:
        print("復活している商品はありませんでした。")

def send_email(items):
    msg = MIMEText("Ciメディカルで以下の商品の在庫が復活した可能性があります！\n\n" + "\n".join(items))
    msg['Subject'] = "【在庫通知】Ciメディカルの商品が入荷しました！"
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.send_message(msg)
        server.quit()
        print("メール送信成功")
    except Exception as e:
        print("メール送信失敗")

if __name__ == "__main__":
    main()
