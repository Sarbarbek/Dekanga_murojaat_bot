"""
Media xavfsizligi moduli.

Telegram bot orqali yuborilgan rasm, video, audio va hujjatlarni
qabul qilishdan avval xavfsizlik tekshiruvidan o'tkazadi.

Tekshiruvlar:
  - Fayl kengaytmasi (whitelist / blacklist)
  - Ikki kengaytmali fayllar (masalan: file.jpg.exe)
  - Fayl o'lchami chegarasi
  - Video davomiyligi chegarasi
  - Caption/izoh ichidagi xavfli patternlar (URL, HTML, skript)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Ruxsat etilgan kengaytmalar ──────────────────────────────────────────────

ALLOWED_DOCUMENT_EXTENSIONS: set[str] = {
    # Hujjatlar
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".rtf", ".odt", ".ods", ".odp", ".csv",
    # Rasmlar
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff",
    # Video
    ".mp4", ".avi", ".mov", ".mkv", ".webm",
    # Audio
    ".mp3", ".ogg", ".wav", ".m4a", ".flac", ".aac",
}

# ── Qat'iy taqiqlangan kengaytmalar ──────────────────────────────────────────

DANGEROUS_EXTENSIONS: set[str] = {
    # Bajariladigan fayllar
    ".exe", ".msi", ".bat", ".cmd", ".com", ".scr", ".pif",
    # Skript fayllar
    ".py", ".js", ".ts", ".vbs", ".vbe", ".wsf", ".wsh",
    ".ps1", ".psm1", ".psd1",
    ".sh", ".bash", ".csh", ".ksh",
    ".rb", ".pl", ".lua",
    # Web / markup (XSS xavfi)
    ".html", ".htm", ".xhtml", ".svg", ".xml", ".xsl",
    ".php", ".asp", ".aspx", ".jsp", ".cgi",
    # Arxivlar (ichida zararli fayl bo'lishi mumkin)
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".cab", ".iso", ".dmg",
    # Mobil
    ".apk", ".ipa", ".aab",
    # Kutubxona / modul
    ".dll", ".so", ".dylib", ".sys", ".drv",
    # Makro bor bo'lishi mumkin
    ".docm", ".xlsm", ".pptm",
    # Boshqa xavfli
    ".reg", ".inf", ".lnk", ".url", ".hta",
    ".jar", ".class", ".war",
}

# ── O'lcham chegaralari (baytlarda) ──────────────────────────────────────────

MAX_PHOTO_SIZE = 5 * 1024 * 1024         # 5 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024        # 50 MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024     # 20 MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024        # 20 MB
MAX_VOICE_SIZE = 10 * 1024 * 1024        # 10 MB

# ── Video davomiyligi chegarasi (soniyalarda) ────────────────────────────────

MAX_VIDEO_DURATION = 180  # 3 daqiqa

# ── Xavfli caption patternlari ───────────────────────────────────────────────

DANGEROUS_CAPTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),        # onclick=, onerror= va h.k.
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"base64", re.IGNORECASE),
    re.compile(r"document\.cookie", re.IGNORECASE),
    re.compile(r"window\.location", re.IGNORECASE),
]


def _format_size(size_bytes: int) -> str:
    """Baytlarni o'qilishi qulay formatga o'giradi."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


@dataclass
class SecurityResult:
    """Xavfsizlik tekshiruvi natijasi."""
    is_safe: bool
    reason: str = ""


class MediaSecurityChecker:
    """Telegram media fayllarni xavfsizlik tekshiruvidan o'tkazadi."""

    # ── Hujjat tekshiruvi ────────────────────────────────────────────────

    def check_document(
        self,
        file_name: str | None,
        file_size: int | None,
        mime_type: str | None = None,
    ) -> SecurityResult:
        """
        Hujjat faylning kengaytmasi, o'lchami va MIME turini tekshiradi.
        """
        if not file_name:
            logger.warning("Hujjat nomi yo'q — bloklandi.")
            return SecurityResult(False, "Fayl nomi aniqlanmadi. Xavfsizlik sababli qabul qilinmadi.")

        file_name_lower = file_name.lower().strip()

        # 1. Ikki kengaytmali fayl tekshiruvi (masalan: photo.jpg.exe)
        suspicious = self._is_double_extension(file_name_lower)
        if suspicious:
            logger.warning(f"Ikki kengaytmali xavfli fayl aniqlandi: {file_name}")
            return SecurityResult(
                False,
                f"⛔ Xavfli fayl aniqlandi: «{file_name}»\n"
                "Ikki kengaytmali fayllar xavfli bo'lishi mumkin."
            )

        # 2. Taqiqlangan kengaytma tekshiruvi
        ext = self._get_extension(file_name_lower)
        if ext in DANGEROUS_EXTENSIONS:
            logger.warning(f"Taqiqlangan kengaytmali fayl: {file_name} ({ext})")
            return SecurityResult(
                False,
                f"⛔ «{ext}» kengaytmali fayllar qabul qilinmaydi.\n"
                "Bu turdagi fayllar xavfli bo'lishi mumkin."
            )

        # 3. Ruxsat etilganlar ro'yxatida borligini tekshirish
        if ext and ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            logger.warning(f"Ruxsat etilmagan kengaytma: {file_name} ({ext})")
            return SecurityResult(
                False,
                f"⛔ «{ext}» kengaytmali fayllar qabul qilinmaydi.\n"
                "Iltimos, quyidagi formatlardan birida yuboring: PDF, DOCX, XLSX, JPG, PNG, MP4, MP3."
            )

        # 4. O'lcham tekshiruvi
        if file_size is not None and file_size > MAX_DOCUMENT_SIZE:
            logger.warning(f"Juda katta hujjat: {file_name} ({_format_size(file_size)})")
            return SecurityResult(
                False,
                f"⛔ Fayl hajmi juda katta ({_format_size(file_size)}).\n"
                f"Maksimal ruxsat etilgan hajm: {_format_size(MAX_DOCUMENT_SIZE)}."
            )

        # 5. MIME type tekshiruvi (agar mavjud bo'lsa)
        if mime_type:
            danger_mimes = {
                "application/x-executable",
                "application/x-msdos-program",
                "application/x-msdownload",
                "application/x-sh",
                "application/x-shellscript",
                "text/html",
                "text/javascript",
                "application/javascript",
                "application/x-httpd-php",
                "application/hta",
            }
            if mime_type.lower() in danger_mimes:
                logger.warning(f"Xavfli MIME turi: {file_name} ({mime_type})")
                return SecurityResult(
                    False,
                    f"⛔ Xavfli fayl turi aniqlandi ({mime_type}).\n"
                    "Bu turdagi fayllar qabul qilinmaydi."
                )

        return SecurityResult(True)

    # ── Rasm tekshiruvi ──────────────────────────────────────────────────

    def check_photo(self, file_size: int | None) -> SecurityResult:
        """Rasm o'lchamini tekshiradi."""
        if file_size is not None and file_size > MAX_PHOTO_SIZE:
            logger.warning(f"Juda katta rasm: {_format_size(file_size)}")
            return SecurityResult(
                False,
                f"⛔ Rasm hajmi juda katta ({_format_size(file_size)}).\n"
                f"Maksimal ruxsat etilgan hajm: {_format_size(MAX_PHOTO_SIZE)}."
            )
        return SecurityResult(True)

    # ── Video tekshiruvi ─────────────────────────────────────────────────

    def check_video(
        self,
        file_size: int | None,
        duration: int | None = None,
    ) -> SecurityResult:
        """Video o'lchami va uzunligini tekshiradi."""
        if file_size is not None and file_size > MAX_VIDEO_SIZE:
            logger.warning(f"Juda katta video: {_format_size(file_size)}")
            return SecurityResult(
                False,
                f"⛔ Video hajmi juda katta ({_format_size(file_size)}).\n"
                f"Maksimal ruxsat etilgan hajm: {_format_size(MAX_VIDEO_SIZE)}."
            )

        if duration is not None and duration > MAX_VIDEO_DURATION:
            minutes = duration // 60
            seconds = duration % 60
            logger.warning(f"Juda uzun video: {minutes} daqiqa {seconds} soniya")
            return SecurityResult(
                False,
                f"⛔ Video juda uzun ({minutes} daqiqa {seconds} soniya).\n"
                f"Maksimal ruxsat etilgan uzunlik: {MAX_VIDEO_DURATION // 60} daqiqa."
            )

        return SecurityResult(True)

    # ── Audio tekshiruvi ─────────────────────────────────────────────────

    def check_audio(self, file_size: int | None) -> SecurityResult:
        """Audio o'lchamini tekshiradi."""
        if file_size is not None and file_size > MAX_AUDIO_SIZE:
            logger.warning(f"Juda katta audio: {_format_size(file_size)}")
            return SecurityResult(
                False,
                f"⛔ Audio hajmi juda katta ({_format_size(file_size)}).\n"
                f"Maksimal ruxsat etilgan hajm: {_format_size(MAX_AUDIO_SIZE)}."
            )
        return SecurityResult(True)

    # ── Ovozli xabar tekshiruvi ──────────────────────────────────────────

    def check_voice(self, file_size: int | None) -> SecurityResult:
        """Ovozli xabar o'lchamini tekshiradi."""
        if file_size is not None and file_size > MAX_VOICE_SIZE:
            logger.warning(f"Juda katta voice: {_format_size(file_size)}")
            return SecurityResult(
                False,
                f"⛔ Ovozli xabar hajmi juda katta ({_format_size(file_size)}).\n"
                f"Maksimal ruxsat etilgan hajm: {_format_size(MAX_VOICE_SIZE)}."
            )
        return SecurityResult(True)

    # ── Caption / izoh tekshiruvi ────────────────────────────────────────

    def check_caption(
        self,
        caption: str | None,
        caption_entities: list | None = None,
    ) -> SecurityResult:
        """
        Izo/caption matnida xavfli pattern borligini tekshiradi.
        URL, HTML teglar, skript va boshqa zararli kontent.
        """
        if not caption:
            return SecurityResult(True)

        # 1. Entitylardagi URL va text_link tekshiruvi
        if caption_entities:
            for entity in caption_entities:
                if entity.type in ("url", "text_link"):
                    logger.warning(f"Captiondan link aniqlandi: {entity.type}")
                    return SecurityResult(
                        False,
                        "⛔ Media izohida linklar aniqlandi.\n"
                        "Xavfsizlik sababli linklardan foydalanish taqiqlangan."
                    )

        # 2. Xavfli pattern tekshiruvi
        for pattern in DANGEROUS_CAPTION_PATTERNS:
            if pattern.search(caption):
                logger.warning(f"Captiondan xavfli pattern aniqlandi: {pattern.pattern}")
                return SecurityResult(
                    False,
                    "⛔ Media izohida xavfli kontent aniqlandi.\n"
                    "Iltimos, faqat oddiy matn yuboring."
                )

        return SecurityResult(True)

    # ── Ichki yordamchi metodlar ─────────────────────────────────────────

    @staticmethod
    def _get_extension(filename: str) -> str:
        """Faylning kengaytmasini ajratib oladi."""
        dot_pos = filename.rfind(".")
        if dot_pos == -1:
            return ""
        return filename[dot_pos:]

    @staticmethod
    def _is_double_extension(filename: str) -> bool:
        """
        Ikki kengaytmali fayllarni aniqlaydi.
        masalan: photo.jpg.exe, report.pdf.bat
        """
        # Nuqtalar bo'yicha ajratamiz
        parts = filename.rsplit(".", maxsplit=2)
        if len(parts) < 3:
            return False

        # Oxirgi kengaytma xavfli bo'lsa
        last_ext = f".{parts[-1]}"
        second_ext = f".{parts[-2]}"

        # Agar oxirgi kengaytma xavfli — albatta bloklash
        if last_ext in DANGEROUS_EXTENSIONS:
            return True

        # Agar ikkinchi kengaytma rasm/hujjat, lekin oxirgi noma'lum — shubhali
        if second_ext in ALLOWED_DOCUMENT_EXTENSIONS and last_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            return True

        return False
