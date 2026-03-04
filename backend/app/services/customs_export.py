"""Экспорт таможенных деклараций ПТД-ЭГ в CSV и PDF."""
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
    """CSV по структуре ПТД-ЭГ для импорта в таможенное ПО."""
    declaration = await _get_declaration(db, declaration_id)

    output = io.StringIO()
    # BOM for Excel
    output.write("\ufeff")

    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "Номер декларации",
        "N п/п",
        "Номер накладной (общая)",
        "Номер накладной (индивид.)",
        "Отправитель",
        "Адрес отправителя",
        "ИНН отправителя",
        "Получатель ФИО",
        "Адрес получателя",
        "Индекс получателя",
        "Телефон получателя",
        "N п/п товара",
        "Наименование товара",
        "Код ТН ВЭД",
        "Страна происхождения",
        "Торговая марка",
        "Количество (шт)",
        "Вес брутто (кг)",
        "Валюта",
        "Стоимость (руб)",
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
            weight_kg = round(item["weight_grams"] * qty / 1000, 3)
            value_rub = round(item["price_kopecks"] * qty / 100, 2)

            value_usd = 0.0
            if declaration.total_value_kopecks > 0 and declaration.total_value_usd_cents > 0:
                ratio = declaration.total_value_usd_cents / declaration.total_value_kopecks
                value_usd = round(item["price_kopecks"] * qty * ratio / 100, 2)

            writer.writerow([
                declaration.number,
                waybill_seq,
                declaration.number,
                order.external_order_id,
                declaration.sender_name,
                declaration.sender_address,
                declaration.sender_inn,
                order.recipient_name,
                order.recipient_address,
                order.recipient_postal_code,
                order.recipient_phone,
                f"{item_global_seq}/{item_in_waybill}",
                item["name"],
                item.get("tn_ved_code", ""),
                item.get("country_of_origin", ""),
                item.get("brand", ""),
                qty,
                weight_kg,
                "RUB",
                value_rub,
                value_usd,
            ])

    # Итоговая строка
    total_weight_kg = round(declaration.total_weight_grams / 1000, 3)
    total_value_rub = round(declaration.total_value_kopecks / 100, 2)
    total_value_usd = round(declaration.total_value_usd_cents / 100, 2)

    writer.writerow([
        "", "", "", "", "", "", "", "", "", "", "",
        "ИТОГО", "", "", "", "",
        "",
        total_weight_kg,
        "RUB",
        total_value_rub,
        total_value_usd,
    ])

    output.seek(0)
    return output


async def generate_pdf(db: AsyncSession, declaration_id: uuid.UUID) -> io.BytesIO:
    """PDF формы ПТД-ЭГ."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
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
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )

    normal = ParagraphStyle("Normal", fontName=font_name, fontSize=8, leading=10)
    heading = ParagraphStyle("Heading", fontName=font_name, fontSize=12, leading=14, spaceAfter=4 * mm)
    small = ParagraphStyle("Small", fontName=font_name, fontSize=7, leading=9)

    elements: list = []

    # Заголовок
    elements.append(Paragraph(
        "ПАССАЖИРСКАЯ ТАМОЖЕННАЯ ДЕКЛАРАЦИЯ (ПТД-ЭГ)", heading
    ))
    elements.append(Paragraph(f"Номер: {declaration.number}", normal))
    elements.append(Paragraph(
        f"Дата: {declaration.created_at.strftime('%d.%m.%Y')}",
        normal,
    ))
    elements.append(Spacer(1, 4 * mm))

    # Отправитель
    sender_data = [
        [Paragraph("<b>ОТПРАВИТЕЛЬ</b>", normal), ""],
        [Paragraph("Наименование:", small), Paragraph(declaration.sender_name, normal)],
        [Paragraph("Адрес:", small), Paragraph(declaration.sender_address, normal)],
        [Paragraph("ИНН:", small), Paragraph(declaration.sender_inn, normal)],
    ]
    t = Table(sender_data, colWidths=[35 * mm, 140 * mm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 3 * mm))

    # Таможенный представитель
    if declaration.customs_rep_name:
        rep_data = [
            [Paragraph("<b>ТАМОЖЕННЫЙ ПРЕДСТАВИТЕЛЬ</b>", normal), ""],
            [Paragraph("Наименование:", small), Paragraph(declaration.customs_rep_name or "", normal)],
            [Paragraph("Свидетельство:", small), Paragraph(declaration.customs_rep_certificate or "", normal)],
        ]
        t = Table(rep_data, colWidths=[35 * mm, 140 * mm])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 3 * mm))

    # Место нахождения товаров
    if declaration.goods_location:
        elements.append(Paragraph(
            f"<b>Место нахождения товаров:</b> {declaration.goods_location}",
            normal,
        ))
        elements.append(Spacer(1, 3 * mm))

    # Таблица товаров
    header = [
        Paragraph("<b>N п/п</b>", small),
        Paragraph("<b>Накладная</b>", small),
        Paragraph("<b>Получатель</b>", small),
        Paragraph("<b>N товара</b>", small),
        Paragraph("<b>Наименование</b>", small),
        Paragraph("<b>ТН ВЭД</b>", small),
        Paragraph("<b>Кол-во</b>", small),
        Paragraph("<b>Вес (кг)</b>", small),
        Paragraph("<b>Стоимость (руб)</b>", small),
    ]

    col_widths = [10 * mm, 22 * mm, 35 * mm, 12 * mm, 38 * mm, 18 * mm, 12 * mm, 15 * mm, 20 * mm]
    table_data = [header]

    waybill_seq = 0
    item_global_seq = 0

    for order in declaration.orders:
        waybill_seq += 1
        item_in_waybill = 0

        for item in order.items:
            item_global_seq += 1
            item_in_waybill += 1

            qty = item["quantity"]
            weight_kg = round(item["weight_grams"] * qty / 1000, 3)
            value_rub = round(item["price_kopecks"] * qty / 100, 2)

            brand_str = f" ({item['brand']})" if item.get("brand") else ""
            name_str = f"{item['name']}{brand_str}"

            row = [
                Paragraph(str(waybill_seq), small),
                Paragraph(order.external_order_id, small),
                Paragraph(f"{order.recipient_name}, {order.recipient_postal_code}", small),
                Paragraph(f"{item_global_seq}/{item_in_waybill}", small),
                Paragraph(name_str, small),
                Paragraph(item.get("tn_ved_code", "—"), small),
                Paragraph(str(qty), small),
                Paragraph(str(weight_kg), small),
                Paragraph(f"{value_rub:.2f}", small),
            ]
            table_data.append(row)

    # Итоговая строка
    total_weight_kg = round(declaration.total_weight_grams / 1000, 3)
    total_value_rub = round(declaration.total_value_kopecks / 100, 2)

    totals_row = [
        "", "", "", "",
        Paragraph("<b>ИТОГО</b>", small),
        "",
        "",
        Paragraph(f"<b>{total_weight_kg}</b>", small),
        Paragraph(f"<b>{total_value_rub:.2f}</b>", small),
    ]
    table_data.append(totals_row)

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
        ("BACKGROUND", (0, -1), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    elements.append(t)

    elements.append(Spacer(1, 6 * mm))

    # Регистрационный номер ФТС
    if declaration.fts_reference:
        elements.append(Paragraph(
            f"<b>Рег. номер ФТС (A):</b> {declaration.fts_reference}",
            normal,
        ))

    # Подпись
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("Подпись: ________________________", normal))
    elements.append(Paragraph(f"Дата: {declaration.created_at.strftime('%d.%m.%Y')}", normal))

    doc.build(elements)
    buffer.seek(0)
    return buffer
