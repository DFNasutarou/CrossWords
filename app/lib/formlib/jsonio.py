import json
from typing import Any, List, Union, Dict


# 再帰的に辞書とリストを許容するデータ型
DataType = Union[int, str, List["DataType"], Dict[str, "DataType"]]


class JsonFileBuilder:
    def __init__(self):
        """
        書き出し先の JSON ファイルパスを指定します。
        """
        self._data: dict[str, DataType] = {}

    def add(self, key, item: DataType) -> None:
        """
        データを順に追加します。
        int, str, リスト, 辞書（キー: str、値: DataType の再帰的構造）を許容。
        """
        self._validate(item)
        self._data[key] = item

    def save(self, path, ensure_ascii: bool = False, indent: int = 2) -> None:
        """
        これまで追加したデータをまとめて JSON ファイルに書き出します。
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=ensure_ascii, indent=indent)

    def load(self, path) -> List[DataType] | None:
        """
        ファイルから読み込んで型チェック後に返します。
        （内部データは上書きしません）
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._validate(data)
        except:
            # ファイルが存在しない
            return None
        return data

    def _validate(self, data: Any) -> None:
        """
        data が許容型かチェックします。
        - int, str
        - list: 各要素を再帰的チェック
        - dict: キーが str、値を再帰的チェック
        """
        if isinstance(data, (int, str)):
            return

        if isinstance(data, list):
            for idx, elem in enumerate(data):
                try:
                    self._validate(elem)
                except TypeError as e:
                    raise TypeError(
                        f"リストの要素 index={idx} が不正です: {e}"
                    )
            return

        if isinstance(data, dict):
            for key, val in data.items():
                if not isinstance(key, str):
                    raise TypeError(
                        f"辞書のキーは str のみ許容します (key={key!r})"
                    )
                try:
                    self._validate(val)
                except TypeError as e:
                    raise TypeError(f"辞書の値 key={key!r} が不正です: {e}")
            return

        raise TypeError(f"許容外の型です: {type(data).__name__}")


# --- 使用例 ---

# if __name__ == "__main__":
#     builder = JsonFileBuilder("with_map.json")

#     builder.add(1)
#     builder.add("two")
#     builder.add([3, "four"])
#     builder.add({"a": 5, "b": ["six", 7], "c": {"nested": 8}})

#     builder.save()

#     loaded = builder.load()
#     print("読み込んだデータ:", loaded)
