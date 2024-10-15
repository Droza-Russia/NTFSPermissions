
# _*_ coding: utf_8 _*_
import json
import math
import os
import sys
from datetime import datetime
import pandas as pd
from winsys import fs


def is_catalog_argument_not_empty(input_json: dict) -> bool:
    """
    Проверяет, не пуст ли аргумент 'Catalog' в входящем JSON-объекте.

    Args:
        input_json (dict): JSON-объект, содержащий аргумент 'Catalog'.

    Returns:
        bool: True, если аргумент 'Catalog' не пуст, False в противном случае.
    """
    return input_json.get('Catalog') is not None and len(input_json.get('Catalog', [])) > 0


def is_path_catalog_exists_and_accessible(input_json: dict) -> bool:
    """
    Проверяет, существует ли путь 'Catalog' в входящем JSON-объекте и доступен ли он для чтения.

    Args:
        input_json (dict): JSON-объект, содержащий путь 'Catalog'.

    Returns:
        bool: True, если путь существует и доступен для чтения, False в противном случае.
    """
    catalog_path = input_json.get('Catalog')
    return os.path.exists(catalog_path) and os.access(catalog_path, os.R_OK)


def read_folder_permissions_from_ntfs(input_json: dict) -> dict:
    """
    Читает права доступа к файлам и папкам в указанной директории из NTFS.

    Args:
        input_json (dict): JSON-объект, содержащий путь к директории.

    Returns:
        dict: Словарь с информацией о файлах и папках, включая права доступа.
    """
    file_collection = []
    catalog_path = input_json.get('Catalog')

    for file in fs.flat(catalog_path):
        file_info = {
            'FileName': os.path.basename(file),
            'FullFilePath': os.path.abspath(file),
            'DateCreated': datetime.fromtimestamp(os.path.getctime(file)).isoformat(),
            'DateLastModified': datetime.fromtimestamp(os.path.getmtime(file)).isoformat(),
            'DateLastOpened': datetime.fromtimestamp(os.path.getatime(file)).isoformat(),
            'SizeFileKB': math.ceil(os.path.getsize(file) / 1024),  # KB
            'Type': 'FOLDER' if os.path.isdir(file) else 'FILE'
        }

        for ace in file.security().dacl:
            access_attributes = fs.FILE_ACCESS.names_from_value(ace.access)
            for access_attr in access_attributes:
                if ace.is_allowed:
                    file_info.setdefault(access_attr, []).append(ace.trustee.name)

        file_collection.append(file_info)

    return {
        "Parent_folder": os.path.basename(catalog_path),
        "Child_files": file_collection
    }


def export_to_excel_sheet(input_data: dict) -> None:
    """
    Экспортирует данные в Excel-файл.

    Args:
        input_data (dict): Словарь с данными для экспорта.
    """
    sheet_name = input_data.get('Parent_folder')
    file_name = f"{datetime.now().strftime('%Y_%m_%d_%H_%M')}_{sheet_name}.xlsx"

    excel_model = pd.DataFrame(input_data['Child_files'])
    excel_model.to_excel(file_name, sheet_name=f"Отчет по директории {sheet_name}", index=False)


def export_to_json(input_data: dict) -> None:
    """
       Экспортирует данные в JSON-файл.

       Args:
           input_data (dict): Словарь с данными для экспорта.
       """

    file_name = f"{datetime.now().strftime('%Y_%m_%d_%H_%M')}_{input_data.get('Parent_folder')}.json"

    with open(file_name, 'w') as f:
        json.dump(input_data, f)


def send_debug_info_for_soar_e4_log_console(input_json: dict) -> None:
    """
    Отправляет отладочную информацию в консоль SOARE4.

    Args:
        input_json (dict): Словарь с данными для отправки.
    """
    debug_info = {
        "Catalog": input_json.get("Catalog"),
        "result": input_json.get("result"),
        "state": input_json.get("state")
    }

    print(json.dumps(debug_info))
    sys.exit(input_json.get('result_index'))


def main(input_json: dict) -> None:
    """
    Основная функция, обрабатывающая входные данные и отправляющая отладочную информацию.

    Args:
        input_json (dict): Словарь с данными для обработки.
    """
    input_json['result'] = "Значение каталога пустое"
    input_json['state'] = 'Ошибка входных параметров'
    input_json['result_index'] = 1

    if is_catalog_argument_not_empty(input_json):
        if is_path_catalog_exists_and_accessible(input_json):
            input_json['result'] = "Значение каталога корректно"
            input_json['state'] = 'Успешно'
            input_json['result_index'] = 0

            response = read_folder_permissions_from_ntfs(input_json)

            if response is not None:
                if input_json.get('Format').lower() == "XLSX".lower():
                    export_to_excel_sheet(response)
                elif input_json.get('Format').lower() == "JSON".lower():
                    export_to_json(response)
            else:
                input_json['result'] = "Права доступа не найдены"
                input_json['state'] = "Ошибка получения атрибутов доступа"

            send_debug_info_for_soar_e4_log_console(input_json)
        else:
            input_json['result'] = f"Искомый каталог {input_json.get('Catalog')} не найден."
            input_json['state'] = 'Ошибка входных параметров'
            send_debug_info_for_soar_e4_log_console(input_json)
    else:
        send_debug_info_for_soar_e4_log_console(input_json)


if __name__ == '__main__':

    # Тестовые данные
    #test_data = {"Catalog": "C:\\ST", "Format": "XLSX"}
    test_data = {"Catalog": "C:\\ST", "Format": "JSON"}
    main(test_data)

    # Для запуска из входных параметров плейбука.
    # main(json.loads(sys.argv[1]))
