import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import sys
import os
import time

# =========================================================
# ★ 金庫（Secrets）から鍵を取り出す（これが超安全なおまじないです！）
# =========================================================
CI_ID = os.getenv("CI_ID")
CI_PASS = os.getenv("CI_PASS")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# 監視したいCiメディカルの商品URL
TARGET_URL = "https://www.ci-medical.com/dental/catalog_item/801Y173"

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
        login_data["login_id"] = CI_ID      # ※もし以前のコードでここが "email" 等だった場合は書き換えてください
        login_data["password"] = CI_PASS

        # ログイン実行
        session.post(login_url, data=login_data, timeout=10)
        print("ログイン通信完了")
        time.sleep(2)

    except Exception as e:
        print(f"ログイン処理でエラー: {e}")
        sys.exit(1)

    print("在庫チェック中...")
    try:
        r = session.get(TARGET_URL, timeout=10)
        r.encoding = r.apparent_encoding

        # ※「入荷待ち」など、在庫がない時に画面に出る言葉を指定してください
        if "入荷待ち" not in r.text: 
            if "Ci" in r.text: # 別ページに飛ばされていないかの安全チェック
                print(f"〇 変化あり（在庫復活の可能性！）: {TARGET_URL}")
                send_email([TARGET_URL])
            else:
                print("× ログイン失敗か別ページに飛ばされています")
        else:
            print(f"× 在庫なし（文言確認）: {TARGET_URL}")

    except Exception as e:
        print(f"取得失敗: {e}")

def send_email(items):
    msg = MIMEText("Ciメディカルで以下の在庫が復活した可能性があります！\n\n" + "\n".join(items))
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
