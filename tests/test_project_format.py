import unittest

from app.project_format import (
    CURRENT_PROJECT_FORMAT_VERSION,
    PREVIOUS_PROJECT_FORMAT_VERSION,
    ProjectFormatError,
    UnsupportedProjectVersion,
    make_project_document,
    read_project_document,
)


class ProjectFormatTest(unittest.TestCase):
    def test_new_document_contains_current_version(self):
        data = {"cell": {}, "key": {}, "world": {}}

        document = make_project_document(data)

        self.assertEqual(
            document["format_version"],
            CURRENT_PROJECT_FORMAT_VERSION,
        )
        self.assertIs(document["data"], data)

    def test_reads_legacy_document_without_version(self):
        data = {"cell": {}, "key": {}, "world": {}}

        self.assertIs(read_project_document({"data": data}), data)

    def test_reads_current_document(self):
        data = {"cell": {}, "key": {}, "world": {}}
        document = {
            "format_version": CURRENT_PROJECT_FORMAT_VERSION,
            "data": data,
        }

        self.assertIs(read_project_document(document), data)

    def test_reads_previous_document(self):
        data = {"cell": {}, "key": {}, "world": {}}
        document = {
            "format_version": PREVIOUS_PROJECT_FORMAT_VERSION,
            "data": data,
        }

        self.assertIs(read_project_document(document), data)

    def test_rejects_future_version(self):
        with self.assertRaises(UnsupportedProjectVersion):
            read_project_document(
                {
                    "format_version": CURRENT_PROJECT_FORMAT_VERSION + 1,
                    "data": {},
                }
            )

    def test_rejects_invalid_document(self):
        with self.assertRaises(ProjectFormatError):
            read_project_document({"format_version": 1})


if __name__ == "__main__":
    unittest.main()
