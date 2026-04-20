from __future__ import annotations

from app.config import Settings


def get_admin_role(settings: Settings, user_id: int) -> str | None:
    """Admin rolini aniqlash: 'kun', 'kech', 'mag' yoki 'total' (super admin uchun)"""
    if user_id in settings.kun_dekan_ids:
        return "kun"
    if user_id in settings.kech_dekan_ids:
        return "kech"
    if user_id in settings.mag_dekan_ids:
        return "mag"
    if user_id in settings.sirt_dekan_ids:
        return "sirt"
    if user_id in settings.med_dekan_ids:
        return "med"
    if user_id in settings.super_admin_ids:
        return "total"
    return None


def is_admin(settings: Settings, user_id: int) -> bool:
    return user_id in settings.admin_ids


def is_super_admin(settings: Settings, user_id: int) -> bool:
    return user_id in settings.super_admin_ids
