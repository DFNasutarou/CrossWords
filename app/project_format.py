PROJECT_DATA_KEY = "data"
PROJECT_FORMAT_VERSION_KEY = "format_version"
CURRENT_PROJECT_FORMAT_VERSION = 2
PREVIOUS_PROJECT_FORMAT_VERSION = 1
LEGACY_PROJECT_FORMAT_VERSION = 0


class ProjectFormatError(ValueError):
    pass


class UnsupportedProjectVersion(ProjectFormatError):
    pass


def make_project_document(data):
    return {
        PROJECT_FORMAT_VERSION_KEY: CURRENT_PROJECT_FORMAT_VERSION,
        PROJECT_DATA_KEY: data,
    }


def read_project_document(document):
    if not isinstance(document, dict) or PROJECT_DATA_KEY not in document:
        raise ProjectFormatError("プロジェクトデータの形式が不正です")

    version = document.get(
        PROJECT_FORMAT_VERSION_KEY,
        LEGACY_PROJECT_FORMAT_VERSION,
    )
    if version not in (
        LEGACY_PROJECT_FORMAT_VERSION,
        PREVIOUS_PROJECT_FORMAT_VERSION,
        CURRENT_PROJECT_FORMAT_VERSION,
    ):
        raise UnsupportedProjectVersion(
            f"未対応のプロジェクト形式です: version {version}"
        )

    data = document[PROJECT_DATA_KEY]
    if not isinstance(data, dict):
        raise ProjectFormatError("プロジェクト本体の形式が不正です")
    return data
