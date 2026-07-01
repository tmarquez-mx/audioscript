import io
import unittest

import pandas as pd

import App


class XlsxExportsTest(unittest.TestCase):
    def test_codes_workbook_contains_dictionary_and_coding_detail(self):
        codes = pd.DataFrame(
            [
                {
                    "codigo": "Acceso",
                    "nota": "Decisión analítica",
                    "cita": "Primera cita",
                    "segmento": 1,
                    "audio": "entrevista.mp3",
                    "fecha_registro": "2026-06-30",
                },
                {
                    "codigo": "Acceso",
                    "nota": "Segundo uso",
                    "cita": "Segunda cita",
                    "segmento": 2,
                    "audio": "entrevista.mp3",
                    "fecha_registro": "2026-06-30",
                },
            ]
        )
        workbook = App.dataframe_to_xlsx_bytes(
            {
                "Diccionario": App.build_codes_import_dataframe(codes),
                "Codificaciones": App.build_codes_detail_dataframe(codes),
            }
        )

        excel_file = pd.ExcelFile(io.BytesIO(workbook))
        self.assertEqual(excel_file.sheet_names, ["Diccionario", "Codificaciones"])

        dictionary = pd.read_excel(io.BytesIO(workbook), sheet_name="Diccionario")
        detail = pd.read_excel(io.BytesIO(workbook), sheet_name="Codificaciones")
        self.assertEqual(dictionary.columns.tolist(), ["Código"])
        self.assertEqual(dictionary["Código"].tolist(), ["Acceso"])
        self.assertEqual(
            detail.columns.tolist(),
            ["Código", "Memo", "Cita", "Segmento", "Audio", "Fecha de registro"],
        )
        self.assertEqual(len(detail), 2)


if __name__ == "__main__":
    unittest.main()
