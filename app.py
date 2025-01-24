import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from pyzbar.pyzbar import decode
from typing import Dict, Any, List
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_pdf(file_path: str) -> List[str]:
    text_data = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    logging.info(f"Текст успешно извлечен с страницы {page_number}")
                    text_data.append({"page": page_number, "text": text.strip()})
                else:
                    logging.warning(f"Текст отсутствует на странице {page_number}")
    except Exception as e:
        logging.error(f"Ошибка при извлечении текста: {e}")
    return text_data

def extract_barcodes_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    barcode_data = []
    try:
        images = convert_from_path(file_path)
        for idx, image in enumerate(images):
            decoded_objects = decode(image)
            if decoded_objects:
                for obj in decoded_objects:
                    barcode_info = {
                        "page": idx + 1,
                        "data": obj.data.decode("utf-8"),
                        "type": obj.type
                    }
                    barcode_data.append(barcode_info)
                    logging.info(f"Баркод найден на странице {idx + 1}: {barcode_info}")
            else:
                logging.info(f"Баркоды отсутствуют на странице {idx + 1}")
    except Exception as e:
        logging.error(f"Ошибка при извлечении баркодов: {e}")
    return barcode_data

def extract_data_from_pdf(file_path: str) -> Dict[str, Any]:
    logging.info(f"Начато извлечение данных из файла {file_path}")
    pdf_data = {
        "text": extract_text_from_pdf(file_path),
        "barcodes": extract_barcodes_from_pdf(file_path)
    }
    logging.info(f"Данные успешно извлечены из {file_path}")
    return pdf_data

def compare_pdf_structure(reference_data: Dict[str, Any], test_data: Dict[str, Any]) -> Dict[str, Any]:
    logging.info("Начинается сравнение структуры PDF")
    comparison_result = {
        "missing_text_pages": [],
        "missing_barcodes": [],
        "additional_text_pages": [],
        "additional_barcodes": [],
        "status": "PASS"
    }

    ref_text_pages = {entry["page"] for entry in reference_data.get("text", [])}
    test_text_pages = {entry["page"] for entry in test_data.get("text", [])}

    comparison_result["missing_text_pages"] = list(ref_text_pages - test_text_pages)
    comparison_result["additional_text_pages"] = list(test_text_pages - ref_text_pages)

    ref_barcodes = {(entry["page"], entry["data"]) for entry in reference_data.get("barcodes", [])}
    test_barcodes = {(entry["page"], entry["data"]) for entry in test_data.get("barcodes", [])}

    comparison_result["missing_barcodes"] = list(ref_barcodes - test_barcodes)
    comparison_result["additional_barcodes"] = list(test_barcodes - ref_barcodes)

    if comparison_result["missing_text_pages"] or comparison_result["missing_barcodes"]:
        comparison_result["status"] = "FAIL"

    logging.info("Сравнение завершено")
    return comparison_result

if __name__ == "__main__":
    reference_file = "/mnt/data/test_task.pdf"
    reference_data = extract_data_from_pdf(reference_file)

    with open("reference_data.json", "w", encoding="utf-8") as ref_file:
        json.dump(reference_data, ref_file, ensure_ascii=False, indent=4)

    logging.info("Эталонные данные сохранены")

    test_file = "test_file.pdf"
    test_data = extract_data_from_pdf(test_file)

    comparison_result = compare_pdf_structure(reference_data, test_data)

    logging.info(f"Результат сравнения: {json.dumps(comparison_result, indent=4, ensure_ascii=False)}")
