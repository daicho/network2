import sys
import socket
import pickle

import mjgame.system as mj
import mjgame.players as mp
import mjgame.graphic as mg

from GameServer import EventKind

# 名前を入力
player_name = input("名前> ")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # サーバーに接続し名前を送信
    s.connect(("localhost", 50005))
    s.sendall(player_name.encode() + EventKind.END)

    while True:
        recv_data = b""

        # データを受信
        while True:
            data = s.recv(4096)
            recv_data += data

            if recv_data[-3:] == EventKind.END:
                break

        # ヘッダと本文を切り離す
        event_kind = recv_data[:3]
        recv_data = recv_data[3:-3]

        # ゲームリーダーのアップデート
        if event_kind == EventKind.UPDATE:
            s.sendall(EventKind.COMPLETE + EventKind.END)
            player = pickle.loads(recv_data)

            screen = mg.Screen(player.game, [player], player, "Mahjong")
            screen.draw()

        # 打牌
        elif event_kind == EventKind.DAHAI:
            ret = player.on_dahai()
            s.sendall(ret.to_bytes(1, "big", signed=True) + EventKind.END)

        # リーチ
        elif event_kind == EventKind.RICHI:
            ret = player.on_richi()
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # ツモ
        elif event_kind == EventKind.TSUMO:
            ret = player.on_tsumo()
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # ロン
        elif event_kind == EventKind.RON:
            ret = player.on_ron(None, None)
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # 暗槓
        elif event_kind == EventKind.ANKAN:
            ret = player.on_ankan(None)
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # 明槓
        elif event_kind == EventKind.MINKAN:
            ret = player.on_minkan(None, None, None)
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # 加槓
        elif event_kind == EventKind.KAKAN:
            ret = player.on_kakan(None)
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # ポン
        elif event_kind == EventKind.PON:
            ret = player.on_pon(None, None, None)
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # チー
        elif event_kind == EventKind.CHI:
            ret = player.on_chi(None, None, None)
            s.sendall(ret.to_bytes(1, "big") + EventKind.END)

        # 終局
        elif event_kind == EventKind.RESULT:
            screen = mg.Screen(player.game, [player], player, "Mahjong")
            screen.draw()

            if input("Press Enter Key...") == "q":
                sys.exit()

            s.sendall(EventKind.COMPLETE + EventKind.END)

        # ゲーム終了
        elif event_kind == EventKind.OVER:
            break
