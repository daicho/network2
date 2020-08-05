import copy
import itertools
import collections
from .core import *

from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter

# 手牌
class Tehai():
    def __init__(self, hais=[], furos=[]):
        self.calculator = Shanten()
        self.hais = hais[:]
        self.furos = furos[:]
        self.tsumo_hai = None
        self.hai_num = len(self.hais)

    # ツモ牌を手牌に格納
    def store(self):
        if self.tsumo_hai is not None:
            self.hais.append(self.tsumo_hai)
            self.tsumo_hai = None

    # ツモ
    def tsumo(self, hai):
        self.store()
        self.tsumo_hai = hai
        self.hai_num = len(self.hais) + 1

    # 追加
    def append(self, hais):
        self.store()
        for hai in hais:
            self.hais.append(hai)
        self.hai_num = len(self.hais)

    # 挿入
    def insert(self, index, hai):
        self.store()
        self.hais.insert(index, hai)
        self.hai_num = len(self.hais)

    # 番号で取り出し
    def pop(self, index=-1):
        self.store()
        pop_hai = self.hais.pop(index)
        self.hai_num = len(self.hais)
        return pop_hai

    # 牌を指定して取り出し
    def remove(self, hai):
        self.store()
        self.hais.remove(hai)
        self.hai_num = len(self.hais)
        return hai

    # 牌の種類を指定して検索
    def find(self, kind, num):
        for hai in self.hais + [self.tsumo_hai]:
            if hai is not None and hai.kind == kind and hai.num == num:
                return hai
        return None

    # 複数の牌を検索
    def find_multi(self, kinds, nums):
        if len(kinds) != len(nums):
            return None

        find_num = len(kinds)
        found_hais = []

        for hai in self.hais + [self.tsumo_hai]:
            if hai is None:
                continue

            for kind, num in zip(kinds, nums):
                if hai.kind == kind and hai.num == num:
                    found_hais.append(hai)
                    kinds.remove(kind)
                    nums.remove(num)
                    break

        if len(found_hais) == find_num:
            return found_hais
        else:
            return None

    # 並べ替え
    def sort(self):
        self.store()
        self.hais.sort()

    # 暗槓可能な牌
    def ankan_able(self):
        return_hais = []

        for hai in self.hais + [self.tsumo_hai]:
            for return_hai in return_hais:
                if hai.kind == return_hai[0].kind and hai.num == return_hai[0].num:
                    break
            else:
                found_hais = self.find_multi([hai.kind for i in range(4)], [hai.num for i in range(4)])

                if found_hais is not None:
                    return_hais.append(found_hais)

        return return_hais

    # 加槓可能な牌
    def kakan_able(self):
        return_hais = []

        for furo in self.furos:
            if furo.kind == FuroKind.PON:
                for hai in self.hais + [self.tsumo_hai]:
                    # 明刻と同じ牌だったら
                    if furo.hais[0].kind == hai.kind and furo.hais[0].num == hai.num:
                        return_hais.append(hai)
                        break

        return return_hais

    # 明槓可能な牌
    def minkan_able(self, target):
        found_hais = self.find_multi([target.kind for i in range(3)], [target.num for i in range(3)])

        if found_hais is None:
            return []
        else:
            return [found_hais]

    # ポン可能な牌
    def pon_able(self, target):
        found_hais = self.find_multi([target.kind for i in range(2)], [target.num for i in range(2)])

        if found_hais is None:
            return []
        else:
            return [found_hais]

    # チー可能な牌
    def chi_able(self, target):
        if target.kind == 3:
            return []

        return_hais = []

        for i in range(-2, 1):
            kinds = []
            nums = []

            for j in range(i, i + 3):
                if j == 0:
                    continue

                kinds.append(target.kind)
                nums.append(target.num + j)

            found_hais = self.find_multi(kinds, nums)

            if found_hais is not None:
                return_hais.append(found_hais)

        return return_hais

    # 暗槓
    def ankan(self, hais):
        append_hais = [self.remove(hai) for hai in hais]
        self.furos.append(Furo(append_hais, FuroKind.ANKAN))
        self.sort()

    # 加槓
    def kakan(self, hai):
        for furo in self.furos:
            if furo.kind == FuroKind.PON:
                # 明刻と同じ牌だったら
                if furo.hais[0].kind == hai.kind and furo.hais[0].num == hai.num:
                    furo.kind = FuroKind.KAKAN
                    furo.hais.append(self.remove(hai))

    # 明槓
    def minkan(self, hais, target, direct):
        append_hais = [self.remove(hai) for hai in hais]
        append_hais.insert(int((direct - 1) * 1.5), target)
        self.furos.append(Furo(append_hais, FuroKind.MINKAN, direct))

    # ポン
    def pon(self, hais, target, direct):
        append_hais = [self.remove(hai) for hai in hais]
        append_hais.insert(direct - 1, target)
        self.furos.append(Furo(append_hais, FuroKind.PON, direct))

    # チー
    def chi(self, hais, target, direct):
        append_hais = [self.remove(hai) for hai in hais]
        append_hais.insert(direct - 1, target)
        self.furos.append(Furo(append_hais, FuroKind.CHI, direct))

    # 表示
    def show(self):
        for hai in self.hais:
            print(format(hai.name, "<4s"), end="")

        if self.tsumo_hai is not None:
            print(" {}".format(self.tsumo_hai.name))
        else:
            print()

        for j in range(len(self.hais)):
            print(format(j, "<4d"), end="")

        if self.tsumo_hai is not None:
            print(" {}".format(j + 1))
        else:
            print()

    # シャンテン数
    def shanten(self):
        tile_strs = [""] * 4

        for hai in self.hais:
            tile_strs[hai.kind] += str(hai.num)

        if self.tsumo_hai is not None:
            tile_strs[self.tsumo_hai.kind] += str(self.tsumo_hai.num)

        tiles = TilesConverter.string_to_34_array(tile_strs[0], tile_strs[1], tile_strs[2], tile_strs[3])

        return self.calculator.calculate_shanten(tiles)
