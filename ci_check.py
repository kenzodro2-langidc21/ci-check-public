import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import sys
import os
import time
import traceback
from datetime import datetime

# ==========================================
# 1. 秘密情報の設定（GitHub Secretsから取得）
# ==========================================
CI_LOGIN_ID = os.getenv("CI_ID")
CI_PASSWORD = os.getenv("CI_PASS")
SENDER_EMAIL = os.getenv("GMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("GMAIL_APP_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

if not all([CI_LOGIN_ID, CI_PASSWORD, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
    print("エラー: GitHub Secretsの設定が足りません！設定を確認してください。")
    sys.exit(1)

TARGET_URLS = [
    "https://www.ci-medical.com/dental/catalog_item/801Y202",
    "https://www.ci-medical.com/dental/catalog_item/801Y201",
    "https://www.ci-medical.com/dental/catalog_item/801Y191",
    "https://www.ci-medical.com/dental/catalog_item/801Y10156",
    "https://www.ci-medical.com/dental/catalog_item/801Y173",
    "https://www.ci-medical.com/dental/catalog_item/801Y458",
    "https://www.ci-medical.com/dental/catalog_item/80126365",
    "https://www.ci-medical.com/dental/catalog_item/80126366",
    "https://www.ci-medical.com/dental/catalog_item/80126364",
    "https://www.ci-medical.com/dental/catalog_item/801128608",
    "https://www.ci-medical.com/dental/catalog_item/801128607",
    "https://www.ci-medical.com/dental/catalog_item/801126940",
    "https://www.ci-medical.com/dental/catalog_item/801126939",
    "https://www.ci-medical.com/dental/catalog_item/801126938",
    "https://www.ci-medical.com/dental/catalog_item/801109528",
    "https://www.ci-medical.com/dental/catalog_item/801109527",
    "https://www.ci-medical.com/dental/catalog_item/80106052",
    "https://www.ci-medical.com/dental/catalog_item/80106051",
    "https://www.ci-medical.com/dental/catalog_item/80106050",
    "https://www.ci-medical.com/dental/catalog_item/8019112",
    "https://www.ci-medical.com/dental/catalog_item/8019111",
    "https://www.ci-medical.com/dental/catalog_item/8019110",
    "https://www.ci-medical.com/dental/catalog_item/8015668",
    "https://www.ci-medical.com/dental/catalog_item/8015667",
    "https://www.ci-medical.com/dental/catalog_item/8015666",
    "https://www.ci-medical.com/dental/catalog_item/8018696",
    "https://www.ci-medical.com/dental/catalog_item/8018695",
    "https://www.ci-medical.com/dental/catalog_item/8018694",
    "https://www.ci-medical.com/dental/catalog_item/801115025",
    "https://www.ci-medical.com/dental/catalog_item/801115026",
    "https://www.ci-medical.com/dental/catalog_item/801115027",
    "https://www.ci-medical.com/dental/catalog_item/80122138",
    "https://www.ci-medical.com/dental/catalog_item/80122137",
    "https://www.ci-medical.com/dental/catalog_item/80122136",
    "https://www.ci-medical.com/dental/catalog_item/8019183",
    "https://www.ci-medical.com/dental/catalog_item/8019182",
    "https://www.ci-medical.com/dental/catalog_item/8019181",
    "https://www.ci-medical.com/dental/catalog_item/80113357",
    "https://www.ci-medical.com/dental/catalog_item/80113356",
    "https://www.ci-medical.com/dental/catalog_item/80113355",
    "https://www.ci-medical.com/dental/catalog_item/801112907",
    "https://www.ci-medical.com/dental/catalog_item/801112908",
    "https://www.ci-medical.com/dental/catalog_item/801112909"
]

login_url = "https://www.ci-medical.com/accounts/sign_in"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Referer": "https://www.ci-medical.com/"
}

def main():
    session = requests.Session()
    session.headers.update(headers)
    
    # --- 1. ログイン処理 ---
    print("ログイン中...")
    try:
        res = session.get(login_url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        login_data = {}
        for hidden_input in soup.find_all("input", type="hidden"):
            if hidden_input.has_attr("name") and hidden_input.has_attr("value"):
                login_data[hidden_input["name"]] = hidden_input["value"]

        login_data["account[login]"] = CI_LOGIN_ID
        login_data["account[password]"] = CI_PASSWORD

        login_res = session.post(login_url, data=login_data, timeout=15)
        login_res.raise_for_status()

        if "ログインできませんでした" in login_res.text or "パスワードが間違っています" in login_res.text:
            raise Exception("ログイン情報が間違っているか、ログインに失敗しました。")
        
        print("ログイン処理完了！")

    except Exception as e:
        print("ログイン処理で致命的なエラーが発生しました:")
        print(traceback.format_exc())
        sys.exit(1)

    # --- 2. 在庫チェック処理 ---
    print("在庫をチェックしています...")
    available_items = []

    for url in TARGET_URLS:
        success = False
        
        for i in range(3):
            try:
                time.sleep(2)
                target_res = session.get(url, timeout=15)
                target_res.raise_for_status()
                target_soup = BeautifulSoup(target_res.content, 'html.parser')
                page_text = target_soup.get_text()

                if "在庫なし" not in page_text:
                    print(f"〇 変化あり（在庫復活の可能性！）: {url}")
                    available_items.append(url)
                else:
                    print(f"× 在庫なし: {url}")
                
                success = True
                break

            except Exception as e:
                print(f"{i+1}回目の取得失敗 ({url}): {e}")
                time.sleep(3)
        if not success:
            print(f"完全に取得失敗: {url}（スキップします）")

    # --- 3. メール送信処理 ---
    if available_items:
        print("在庫が復活した商品があったので、メールを送信します！")
        send_email(available_items)
    else:
        print("現在、すべての商品は「在庫なし」でした。")

def send_email(items):
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    subject = f"【在庫通知】Ciメディカルの商品が入荷しました！ {current_time}"
    
    body = "以下の商品の在庫が復活した可能性があります。\n\n"
    for item in items:
        body += f"・{item}\n"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("通知メールの送信が完了しました！")
    except Exception as e:
        print("メールの送信に失敗しました:")
        print(traceback.format_exc())
        print("※GitHub Secretsの「GMAIL_APP_PASS」が正しく設定されているか確認してください。")
        sys.exit(1)

if __name__ == "__main__":
    main()
