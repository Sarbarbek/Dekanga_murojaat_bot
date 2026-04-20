"""
app/media_security.py moduli uchun unit testlar.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.media_security import (
    MediaSecurityChecker,
    MAX_PHOTO_SIZE,
    MAX_VIDEO_SIZE,
    MAX_DOCUMENT_SIZE,
    MAX_AUDIO_SIZE,
    MAX_VOICE_SIZE,
    MAX_VIDEO_DURATION,
)


@pytest.fixture
def checker():
    return MediaSecurityChecker()


# ─── check_document testlari ────────────────────────────────────────────────


class TestCheckDocument:
    def test_allowed_pdf_passes(self, checker):
        result = checker.check_document("report.pdf", 1024)
        assert result.is_safe is True

    def test_allowed_docx_passes(self, checker):
        result = checker.check_document("homework.docx", 2048)
        assert result.is_safe is True

    def test_allowed_xlsx_passes(self, checker):
        result = checker.check_document("grades.xlsx", 5000)
        assert result.is_safe is True

    def test_dangerous_exe_blocked(self, checker):
        result = checker.check_document("virus.exe", 1024)
        assert result.is_safe is False
        assert "exe" in result.reason.lower()

    def test_dangerous_bat_blocked(self, checker):
        result = checker.check_document("hack.bat", 512)
        assert result.is_safe is False

    def test_dangerous_py_blocked(self, checker):
        result = checker.check_document("malware.py", 100)
        assert result.is_safe is False

    def test_dangerous_html_blocked(self, checker):
        result = checker.check_document("phishing.html", 4096)
        assert result.is_safe is False

    def test_dangerous_apk_blocked(self, checker):
        result = checker.check_document("app.apk", 5_000_000)
        assert result.is_safe is False

    def test_dangerous_zip_blocked(self, checker):
        result = checker.check_document("archive.zip", 1000)
        assert result.is_safe is False

    def test_unknown_extension_blocked(self, checker):
        result = checker.check_document("data.xyz", 100)
        assert result.is_safe is False

    def test_no_filename_blocked(self, checker):
        result = checker.check_document(None, 1024)
        assert result.is_safe is False

    def test_oversized_document_blocked(self, checker):
        result = checker.check_document("big.pdf", MAX_DOCUMENT_SIZE + 1)
        assert result.is_safe is False
        assert "hajm" in result.reason.lower()

    def test_double_extension_exe_blocked(self, checker):
        result = checker.check_document("photo.jpg.exe", 1024)
        assert result.is_safe is False
        assert "kengaytmali" in result.reason.lower()

    def test_double_extension_bat_blocked(self, checker):
        result = checker.check_document("report.pdf.bat", 1024)
        assert result.is_safe is False

    def test_dangerous_mime_type_blocked(self, checker):
        result = checker.check_document("file.pdf", 1024, "application/x-msdownload")
        assert result.is_safe is False

    def test_safe_mime_passes(self, checker):
        result = checker.check_document("file.pdf", 1024, "application/pdf")
        assert result.is_safe is True

    def test_docm_macro_blocked(self, checker):
        result = checker.check_document("macro.docm", 1024)
        assert result.is_safe is False


# ─── check_photo testlari ───────────────────────────────────────────────────


class TestCheckPhoto:
    def test_normal_photo_passes(self, checker):
        result = checker.check_photo(500_000)  # 500 KB
        assert result.is_safe is True

    def test_oversized_photo_blocked(self, checker):
        result = checker.check_photo(MAX_PHOTO_SIZE + 1)
        assert result.is_safe is False
        assert "hajm" in result.reason.lower()

    def test_none_size_passes(self, checker):
        result = checker.check_photo(None)
        assert result.is_safe is True

    def test_exact_max_passes(self, checker):
        result = checker.check_photo(MAX_PHOTO_SIZE)
        assert result.is_safe is True


# ─── check_video testlari ───────────────────────────────────────────────────


class TestCheckVideo:
    def test_normal_video_passes(self, checker):
        result = checker.check_video(10_000_000, 60)  # 10 MB, 1 min
        assert result.is_safe is True

    def test_oversized_video_blocked(self, checker):
        result = checker.check_video(MAX_VIDEO_SIZE + 1, 30)
        assert result.is_safe is False

    def test_too_long_video_blocked(self, checker):
        result = checker.check_video(1_000_000, MAX_VIDEO_DURATION + 1)
        assert result.is_safe is False
        assert "uzun" in result.reason.lower()

    def test_none_values_pass(self, checker):
        result = checker.check_video(None, None)
        assert result.is_safe is True


# ─── check_audio testlari ───────────────────────────────────────────────────


class TestCheckAudio:
    def test_normal_audio_passes(self, checker):
        result = checker.check_audio(3_000_000)
        assert result.is_safe is True

    def test_oversized_audio_blocked(self, checker):
        result = checker.check_audio(MAX_AUDIO_SIZE + 1)
        assert result.is_safe is False


# ─── check_voice testlari ───────────────────────────────────────────────────


class TestCheckVoice:
    def test_normal_voice_passes(self, checker):
        result = checker.check_voice(500_000)
        assert result.is_safe is True

    def test_oversized_voice_blocked(self, checker):
        result = checker.check_voice(MAX_VOICE_SIZE + 1)
        assert result.is_safe is False


# ─── check_caption testlari ─────────────────────────────────────────────────


class TestCheckCaption:
    def test_empty_caption_passes(self, checker):
        result = checker.check_caption(None)
        assert result.is_safe is True

    def test_safe_caption_passes(self, checker):
        result = checker.check_caption("Salom, mening murojaatim.")
        assert result.is_safe is True

    def test_url_entity_blocked(self, checker):
        entity = MagicMock()
        entity.type = "url"
        result = checker.check_caption("Visit http://example.com", [entity])
        assert result.is_safe is False
        assert "link" in result.reason.lower()

    def test_text_link_entity_blocked(self, checker):
        entity = MagicMock()
        entity.type = "text_link"
        result = checker.check_caption("Click here", [entity])
        assert result.is_safe is False

    def test_script_tag_blocked(self, checker):
        result = checker.check_caption("<script>alert('xss')</script>")
        assert result.is_safe is False

    def test_javascript_blocked(self, checker):
        result = checker.check_caption("javascript:alert(1)")
        assert result.is_safe is False

    def test_iframe_blocked(self, checker):
        result = checker.check_caption("<iframe src='evil.com'></iframe>")
        assert result.is_safe is False

    def test_onclick_blocked(self, checker):
        result = checker.check_caption('onerror="steal()"')
        assert result.is_safe is False

    def test_eval_blocked(self, checker):
        result = checker.check_caption("eval(malicious_code)")
        assert result.is_safe is False

    def test_base64_blocked(self, checker):
        result = checker.check_caption("data:text/html;base64,PHNjcmlw")
        assert result.is_safe is False


# ─── _is_double_extension testlari ──────────────────────────────────────────


class TestDoubleExtension:
    def test_single_extension_safe(self, checker):
        assert checker._is_double_extension("file.pdf") is False

    def test_no_extension_safe(self, checker):
        assert checker._is_double_extension("file") is False

    def test_jpg_exe_detected(self, checker):
        assert checker._is_double_extension("photo.jpg.exe") is True

    def test_pdf_bat_detected(self, checker):
        assert checker._is_double_extension("report.pdf.bat") is True

    def test_jpg_png_safe(self, checker):
        """Ikkala kengaytma ham ruxsat etilgan — xavfsiz."""
        assert checker._is_double_extension("image.jpg.png") is False

    def test_doc_sh_detected(self, checker):
        assert checker._is_double_extension("doc.pdf.sh") is True
