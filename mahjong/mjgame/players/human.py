import sys
from .. import system as mj

# 人間
class Human(mj.Player):
    def __init__(self):
        super().__init__()
        self.name = "Human"

    # 確認メッセージを表示
    def confirm(self, message, default=True):
        while True:
            select_input = input("{} [{}]> ".format(message, "Y/n" if default else "y/N"))

            if select_input == "":
                return default

            elif select_input == "Y" or select_input == "y":
                return True

            elif select_input == "N" or select_input == "n":
                return False

    # 選択
    def on_dahai(self):
        # 入力
        while True:
            select_input = input("> ")

            if select_input == "q":
                sys.exit()

            # ツモ切り
            elif select_input == "":
                return -1

            elif select_input.isdecimal() and 0 <= int(select_input) <= self.tehai.hai_num:
                break

        return int(select_input)

    # 立直
    def on_richi(self):
        return self.confirm("立直する？", False)

    # ツモ和了
    def on_tsumo(self):
        return self.confirm("ツモる？", True)

    # ロン和了
    def on_ron(self, target, whose):
        return self.confirm("ロンする？", True)

    # 暗槓
    def on_ankan(self, target):
        return self.confirm("暗槓する？", False)

    # 明槓
    def on_minkan(self, hais, target, whose):
        return self.confirm("明槓する？", False)

    # 加槓
    def on_kakan(self, target):
        return self.confirm("加槓する？", False)

    # ポン
    def on_pon(self, hais, target, whose):
        return self.confirm("ポンする？", False)

    # チー
    def on_chi(self, hais, target, whose):
        return self.confirm("チーする？", False)
