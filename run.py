import os
import sys
import subprocess
import shutil

def setup_and_run():
    # Skript joylashgan asosiy papkaga o'tib olish
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 50)
    print("🚀 Dekanga Murojaat Botini Ishga Tushirish")
    print("=" * 50)

    # 1. .env faylini tekshirish
    if not os.path.exists(".env"):
        print("⚠️ '.env' fayli topilmadi!")
        if os.path.exists(".env.example"):
            print("📋 '.env.example' dan qo'llanma sifatida nusxa olinmoqda ('.env' nomiga)...")
            shutil.copy(".env.example", ".env")
            print("❌ DASTUR TO'XTATILDI!")
            print("👉 Endi iltimos, papkadagi '.env' faylini oching va ichiga BOT_TOKEN hamda ma'lumotlar bazasi (PostgreSQL) ma'lumotlarini kiriting.")
            print("👉 So'ngra qaytadan 'python run.py' ni ishga tushiring.")
            sys.exit(1)
        else:
            print("❌ Muhit o'zgaruvchilari fayli topilmadi. Dastur to'xtatildi.")
            sys.exit(1)

    # 2. Kutubxonalarni o'rnatish (requirements.txt)
    print("\n📦 Kerakli kutubxonalar va ularning versiyalari tekshirilmoqda...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])
        print("✅ Barcha kutubxonalar o'rnatilgan va tayyor halatda!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Kutubxonalarni o'rnatishda xato: {e}")
        print("Iltimos, internet aloqasini tekshiring va 'pip install -r requirements.txt' ni qo'lda yozib ko'ring.")
        sys.exit(1)

    # 3. Asosiy dasturni ishga tushirish
    print("\n🟢 Bot (main.py) ishga tushirilmoqda. Muvaffaqiyatli ishlashni boshlasa, xabarlar jurnali (logs) paydo bo'ladi...\n")
    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n🛑 Dastur foydalanuvchi tomonidan to'xtatildi (Ctrl+C).")
    except Exception as e:
        print(f"\n❌ Dastur ishlashida xatolik yuz berdi: {e}")

if __name__ == "__main__":
    setup_and_run()
