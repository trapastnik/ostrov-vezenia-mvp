"""Экспорт таможенных деклараций ДТЭГ в CSV и PDF (Решение ЕЭК №142)."""
import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customs_declaration import CustomsDeclaration


async def _get_declaration(db: AsyncSession, declaration_id: uuid.UUID) -> CustomsDeclaration:
    from fastapi import HTTPException

    result = await db.execute(
        select(CustomsDeclaration)
        .where(CustomsDeclaration.id == declaration_id)
        .options(selectinload(CustomsDeclaration.orders))
    )
    declaration = result.scalar_one_or_none()
    if not declaration:
        raise HTTPException(404, "Декларация не найдена")
    return declaration


async def generate_csv(db: AsyncSession, declaration_id: uuid.UUID) -> io.StringIO:
    """CSV по структуре ДТЭГ (Решение ЕЭК №142) для импорта в таможенное ПО."""
    declaration = await _get_declaration(db, declaration_id)

    output = io.StringIO()
    # BOM for Excel
    output.write("\ufeff")

    writer = csv.writer(output, delimiter=";")

    # Заголовок CSV соответствует колонкам ДТЭГ
    writer.writerow([
        # Шапка
        "Номер ДТЭГ",
        "Процедура",
        # Колонки 1–5: Общие сведения
        "1. N п/п",
        "2. Номер общей накладной",
        "3. Номер индивид. накладной",
        "4. Отправитель",
        "4. ИНН отправителя",
        "4. Адрес отправителя",
        "5. Получатель ФИО",
        "5. Адрес получателя",
        "5. Индекс получателя",
        "5. Телефон получателя",
        "5. Паспорт серия",
        "5. Паспорт номер",
        # Колонки 6–13: Сведения о товарах
        "6. N п/п товара",
        "7. Наименование товара",
        "8. Код ТН ВЭД",
        "Страна происхождения",
        "Торговая марка",
        "9. Доп. единицы",
        "10. Масса брутто (кг)",
        "11. Масса нетто (кг)",
        "12. Валюта / Стоимость",
        "13. Таможенная стоимость (руб)",
        "Стоимость (USD)",
    ])

    waybill_seq = 0
    item_global_seq = 0

    for order in declaration.orders:
        waybill_seq += 1
        item_in_waybill = 0

        for item in order.items:
            item_global_seq += 1
            item_in_waybill += 1

            qty = item["quantity"]
            weight_brutto_kg = round(item["weight_grams"] * qty / 1000, 3)
            # Для товаров ≤200 EUR масса нетто = масса брутто (п.27 ДТЭГ)
            weight_netto_kg = weight_brutto_kg
            value_rub = round(item["price_kopecks"] * qty / 100, 2)
            # Таможенная стоимость = стоимость товара (для ≤200 EUR)
            customs_value_rub = value_rub

            value_usd = 0.0
            if declaration.total_value_kopecks > 0 and declaration.total_value_usd_cents > 0:
                ratio = declaration.total_value_usd_cents / declaration.total_value_kopecks
                value_usd = round(item["price_kopecks"] * qty * ratio / 100, 2)

            writer.writerow([
                declaration.number,
                "4000",  # Импорт для внутреннего потребления
                waybill_seq,
                declaration.number,
                order.external_order_id,
                declaration.sender_name,
                declaration.sender_inn,
                declaration.sender_address,
                order.recipient_name,
                order.recipient_address,
                order.recipient_postal_code,
                order.recipient_phone,
                order.recipient_passport_series or "",
                order.recipient_passport_number or "",
                f"{item_global_seq}/{item_in_waybill}",
                item["name"],
                item.get("tn_ved_code", ""),
                item.get("country_of_origin", ""),
                item.get("brand", ""),
                "",  # Доп. единицы (не обязательно при ≤200 EUR)
                weight_brutto_kg,
                weight_netto_kg,
                f"RUB / {value_rub:.2f}",
                customs_value_rub,
                value_usd,
            ])

    # Итоговая строка
    total_weight_kg = round(declaration.total_weight_grams / 1000, 3)
    total_value_rub = round(declaration.total_value_kopecks / 100, 2)
    total_value_usd = round(declaration.total_value_usd_cents / 100, 2)

    writer.writerow([
        "", "", "", "", "", "", "", "", "", "", "", "", "", "",
        "ИТОГО", "", "", "", "", "",
        total_weight_kg,
        total_weight_kg,
        f"RUB / {total_value_rub:.2f}",
        total_value_rub,
        total_value_usd,
    ])

    output.seek(0)
    return output


async def generate_pdf(db: AsyncSession, declaration_id: uuid.UUID) -> io.BytesIO:
    """PDF формы ДТЭГ (Решение ЕЭК №142)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    declaration = await _get_declaration(db, declaration_id)

    # Регистрация кириллического шрифта (regular + bold)
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    font_path = os.path.join(fonts_dir, "DejaVuSans.ttf")
    font_bold_path = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")
    if os.path.exists(font_path):
        if "DejaVu" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("DejaVu", font_path))
            bold = font_bold_path if os.path.exists(font_bold_path) else font_path
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
            from reportlab.lib.fonts import addMapping
            addMapping("DejaVu", 0, 0, "DejaVu")       # normal
            addMapping("DejaVu", 1, 0, "DejaVu-Bold")   # bold
        font_name = "DejaVu"
    else:
        font_name = "Helvetica"

    buffer = io.BytesIO()
    # Альбомная ориентация для ДТЭГ (больше колонок)
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=10 * mm, rightMargin=10 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
    )

    normal = ParagraphStyle("Normal", fontName=font_name, fontSize=8, leading=10)
    heading = ParagraphStyle("Heading", fontName=font_name, fontSize=11, leading=13, spaceAfter=3 * mm)
    small = ParagraphStyle("Small", fontName=font_name, fontSize=6.5, leading=8)
    small_bold = ParagraphStyle("SmallBold", fontName=font_name, fontSize=6.5, leading=8)

    elements: list = []

    # ===== ЗАГОЛОВОК =====
    elements.append(Paragraph(
        "ДЕКЛАРАЦИЯ НА ТОВАРЫ ДЛЯ ЭКСПРЕСС-ГРУЗОВ (ДТЭГ)", heading
    ))
    elements.append(Paragraph(
        f"<b>Номер:</b> {declaration.number} &nbsp;&nbsp;&nbsp; "
        f"<b>Дата:</b> {declaration.created_at.strftime('%d.%m.%Y')} &nbsp;&nbsp;&nbsp; "
        f"<b>Процедура:</b> 40 00",
        normal,
    ))
    elements.append(Spacer(1, 3 * mm))

    # ===== РАЗДЕЛ A — Регистрационный номер ФТС =====
    if declaration.fts_reference:
        elements.append(Paragraph(
            f"<b>A. Рег. номер ФТС:</b> {declaration.fts_reference}", normal
        ))
        elements.append(Spacer(1, 2 * mm))

    # ===== ШАПКА: Отправитель / Получатель / Таможенный представитель =====
    header_data = [
        [
            Paragraph("<b>ОТПРАВИТЕЛЬ (по общей накладной)</b>", small),
            Paragraph("<b>ТАМОЖЕННЫЙ ПРЕДСТАВИТЕЛЬ</b>", small),
            Paragraph("<b>МЕСТО НАХОЖДЕНИЯ ТОВАРОВ</b>", small),
        ],
        [
            Paragraph(
                f"{declaration.sender_name}<br/>"
                f"{declaration.sender_address}<br/>"
                f"ИНН: {declaration.sender_inn}",
                small,
            ),
            Paragraph(
                f"{declaration.customs_rep_name or '—'}<br/>"
                f"Свид.: {declaration.customs_rep_certificate or '—'}",
                small,
            ),
            Paragraph(declaration.goods_location or "—", small),
        ],
    ]
    t = Table(header_data, colWidths=[100 * mm, 90 * mm, 80 * mm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 3 * mm))

    # ===== ТАБЛИЦА ТОВАРОВ (колонки 1–13 ДТЭГ) =====
    table_header = [
        Paragraph("<b>1<br/>N п/п</b>", small),
        Paragraph("<b>2<br/>Общая накл.</b>", small),
        Paragraph("<b>3<br/>Индивид. накл.</b>", small),
        Paragraph("<b>5. Получатель</b>", small),
        Paragraph("<b>6<br/>N товара</b>", small),
        Paragraph("<b>7. Наименование</b>", small),
        Paragraph("<b>8<br/>ТН ВЭД</b>", small),
        Paragraph("<b>Страна</b>", small),
        Paragraph("<b>10<br/>Брутто (кг)</b>", small),
        Paragraph("<b>11<br/>Нетто (кг)</b>", small),
        Paragraph("<b>12<br/>Валюта / Стоимость</b>", small),
        Paragraph("<b>13<br/>Там. стоимость</b>", small),
    ]

    col_widths = [
        10 * mm,   # 1. N п/п
        20 * mm,   # 2. Общая накладная
        22 * mm,   # 3. Индивид. накладная
        38 * mm,   # 5. Получатель
        12 * mm,   # 6. N товара
        42 * mm,   # 7. Наименование
        16 * mm,   # 8. ТН ВЭД
        10 * mm,   # Страна
        16 * mm,   # 10. Брутто
        16 * mm,   # 11. Нетто
        24 * mm,   # 12. Валюта/Стоимость
        22 * mm,   # 13. Там. стоимость
    ]
    table_data = [table_header]

    waybill_seq = 0
    item_global_seq = 0

    for order in declaration.orders:
        waybill_seq += 1
        item_in_waybill = 0

        for item in order.items:
            item_global_seq += 1
            item_in_waybill += 1

            qty = item["quantity"]
            weight_brutto_kg = round(item["weight_grams"] * qty / 1000, 3)
            weight_netto_kg = weight_brutto_kg  # При ≤200 EUR нетто = брутто
            value_rub = round(item["price_kopecks"] * qty / 100, 2)
            customs_value_rub = value_rub  # При ≤200 EUR таможенная стоимость = стоимость

            brand_str = f" ({item['brand']})" if item.get("brand") else ""
            name_str = f"{item['name']}{brand_str}"

            row = [
                Paragraph(str(waybill_seq), small),
                Paragraph(declaration.number, small),
                Paragraph(order.external_order_id, small),
                Paragraph(
                    f"{order.recipient_name}<br/>"
                    f"{order.recipient_postal_code}<br/>"
                    f"П: {order.recipient_passport_series or '?'} "
                    f"{order.recipient_passport_number or '?'}",
                    small,
                ),
                Paragraph(f"{item_global_seq}/{item_in_waybill}", small),
                Paragraph(name_str, small),
                Paragraph(item.get("tn_ved_code", "—"), small),
                Paragraph(item.get("country_of_origin", "—"), small),
                Paragraph(str(weight_brutto_kg), small),
                Paragraph(str(weight_netto_kg), small),
                Paragraph(f"RUB<br/>{value_rub:.2f}", small),
                Paragraph(f"RUB<br/>{customs_value_rub:.2f}", small),
            ]
            table_data.append(row)

    # Итоговая строка
    total_weight_kg = round(declaration.total_weight_grams / 1000, 3)
    total_value_rub = round(declaration.total_value_kopecks / 100, 2)
    total_value_usd = round(declaration.total_value_usd_cents / 100, 2)

    totals_row = [
        "", "", "", "",
        "",
        Paragraph("<b>ИТОГО</b>", small),
        "",
        "",
        Paragraph(f"<b>{total_weight_kg}</b>", small),
        Paragraph(f"<b>{total_weight_kg}</b>", small),
        Paragraph(f"<b>RUB<br/>{total_value_rub:.2f}</b>", small),
        Paragraph(f"<b>RUB<br/>{total_value_rub:.2f}</b>", small),
    ]
    table_data.append(totals_row)

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
        ("BACKGROUND", (0, -1), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
    ]))
    elements.append(t)

    elements.append(Spacer(1, 4 * mm))

    # ===== Эквиваленты валют (справочно) =====
    total_value_eur = round(declaration.total_value_eur_cents / 100, 2) if declaration.total_value_eur_cents else 0
    elements.append(Paragraph(
        f"<b>Справочно:</b> {total_value_eur:.2f} EUR &nbsp;&nbsp;/&nbsp;&nbsp; {total_value_usd:.2f} USD",
        normal,
    ))

    elements.append(Spacer(1, 4 * mm))

    # ===== РАЗДЕЛ B — Исчисление платежей =====
    elements.append(Paragraph("<b>B. ИСЧИСЛЕНИЕ ТАМОЖЕННЫХ ПОШЛИН, НАЛОГОВ, СБОРОВ</b>", normal))
    elements.append(Spacer(1, 2 * mm))

    b_header = [
        Paragraph("<b>Товар</b>", small),
        Paragraph("<b>Код вида платежа</b>", small),
        Paragraph("<b>База исчисления</b>", small),
        Paragraph("<b>Ед. изм.</b>", small),
        Paragraph("<b>Ставка</b>", small),
        Paragraph("<b>Сумма (руб)</b>", small),
    ]
    b_data = [b_header]
    # При ≤200 EUR пошлина = 0, добавляем одну строку-заглушку
    b_data.append([
        Paragraph("—", small),
        Paragraph("—", small),
        Paragraph("—", small),
        Paragraph("—", small),
        Paragraph("0%", small),
        Paragraph("0.00", small),
    ])

    b_widths = [50 * mm, 30 * mm, 40 * mm, 20 * mm, 25 * mm, 30 * mm]
    t_b = Table(b_data, colWidths=b_widths)
    t_b.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(t_b)

    elements.append(Spacer(1, 4 * mm))

    # ===== РАЗДЕЛ B1 — Подробности уплаты =====
    elements.append(Paragraph(
        "<b>B1. Подробности уплаты:</b> Не применимо (товары ≤200 EUR, пошлина 0%)",
        normal,
    ))

    elements.append(Spacer(1, 6 * mm))

    # ===== Лицо, заполнившее ДТЭГ =====
    signer_data = [
        [Paragraph("<b>Сведения о лице, заполнившем ДТЭГ</b>", small), "", ""],
        [
            Paragraph("Таможенный представитель:", small),
            Paragraph(declaration.customs_rep_name or "—", small),
            Paragraph(f"Свид.: {declaration.customs_rep_certificate or '—'}", small),
        ],
        [
            Paragraph("Подпись:", small),
            Paragraph("________________________", small),
            Paragraph(f"Дата: {declaration.created_at.strftime('%d.%m.%Y')}", small),
        ],
    ]
    t_s = Table(signer_data, colWidths=[55 * mm, 80 * mm, 60 * mm])
    t_s.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("SPAN", (0, 0), (-1, 0)),
    ]))
    elements.append(t_s)

    elements.append(Spacer(1, 4 * mm))

    # ===== Разделы C и D (заполняются таможней) =====
    cd_data = [
        [
            Paragraph("<b>C. Сведения о выпуске / отказе</b>", small),
            Paragraph("<b>D. Прочие отметки</b>", small),
        ],
        [
            Paragraph("(заполняется таможенным органом)", small),
            Paragraph("(заполняется таможенным органом)", small),
        ],
    ]
    t_cd = Table(cd_data, colWidths=[130 * mm, 130 * mm])
    t_cd.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, 1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 20),
    ]))
    elements.append(t_cd)

    # Примечание оператора
    if declaration.operator_note:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(
            f"<b>Примечание:</b> {declaration.operator_note}", normal
        ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
