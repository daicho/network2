import enum

# 河
class Kawa():
    def __init__(self):
        self.hais = []

    # 追加
    def append(self, hai, tsumogiri=False, richi=False):
        self.hais.append(KawaHai(hai, tsumogiri, richi))

# 河の麻雀牌
class KawaHai():
    def __init__(self, hai, tsumogiri=False, richi=False):
        self.hai = hai
        self.tsumogiri = tsumogiri
        self.richi = richi
        self.furo = False
        self.hoju = False

# ゲームリーダー
class GameReader():
    def __init__(self, hai_set, player_num, start_point):
        self.hai_set = hai_set
        self.player_num = player_num
        self.start_point = start_point

        self.bakaze = 0
        self.kyoku = 0
        self.honba = 0
        self.kyotaku = 0

        self.players = [PlayerReader(i) for i in range(self.player_num)]
        self.turn = 0
        self.cur_player = self.players[self.turn]

        self.yama_remain = 0
        self.dora_hais = []
        self.uradora_hais = None
        self.doras = []
        self.uradoras = None

# プレイヤーリーダー
class PlayerReader():
    def __init__(self, chicha):
        self.name = ""
        self.chicha = chicha
        self.point = 0
        self.tehai = TehaiReader()
        self.kawa = Kawa()
        self.richi = False
        self.furo = False
        self.ippatsu = False

# 手牌リーダー
class TehaiReader():
    def __init__(self):
        self.hais = None
        self.furos = []
        self.hai_num = 0
        self.tsumo_hai = None
        self.exist_tsumo_hai = False

# 副露
class Furo():
    def __init__(self, hais, kind, direct=0):
        self.hais = hais
        self.kind = kind
        self.direct = direct

# 副露の種類
class FuroKind(enum.Enum):
    PON = enum.auto()
    CHI = enum.auto()
    ANKAN = enum.auto()
    MINKAN = enum.auto()
    KAKAN = enum.auto()

# 麻雀牌
class Hai():
    """
    kind:
      0 ... 索子
      1 ... 筒子
      2 ... 萬子
      3 ... 字牌

    num:
      1-9 ... 数字
      or
      1-7 ... 東～中
    """

    def __init__(self, kind, num, red=False):
        self.kind = kind # 種類
        self.num = num   # 数字
        self.red = red   # 赤ドラかどうか

        COLOR_NAME = ["s", "p", "m"]
        JIHAI_NAME = ["Ton", "Nan", "Sha", "Pei", "Hak", "Hat", "Chu"]

        # 名称
        if self.kind <= 2:
            self.name = "{}{}{}".format(
                COLOR_NAME[self.kind],
                self.num,
                "@" if self.red else ""
            )
        else:
            self.name = "{}{}".format(
                JIHAI_NAME[self.num - 1],
                "@" if self.red else ""
            )

    # 比較演算子
    def __eq__(self, other):
        return (self.kind, self.num, self.red) == (other.kind, other.num, other.red)

    def __lt__(self, other):
        return (self.kind, self.num, self.red) < (other.kind, other.num, other.red)

    def __gt__(self, other):
        return (self.kind, self.num, self.red) > (other.kind, other.num, other.red)
