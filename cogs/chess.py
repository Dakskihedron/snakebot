from discord.ext import commands
import discord
import re
import time
from itertools import count
from collections import namedtuple
import io
from PIL import Image, ImageDraw, ImageFont
import asyncio
import cogs.utils.database as DB

# Source
# https://github.com/thomasahle/sunfish/blob/master/LICENSE.md
# https://github.com/thomasahle/sunfish
# Modified a little to work with discord

# fmt: off

piece = {'P': 100, 'N': 280, 'B': 320, 'R': 479, 'Q': 929, 'K': 60000}
pst = {
    'P': (0,   0,   0,   0,   0,   0,   0,   0,
          78,  83,  86,  73, 102,  82,  85,  90,
          7,  29,  21,  44,  40,  31,  44,   7,
          -17,  16,  -2,  15,  14,   0,  15, -13,
          -26,   3,  10,   9,   6,   1,   0, -23,
          -22,   9,   5, -11, -10,  -2,   3, -19,
          -31,   8,  -7, -37, -36, -14,   3, -31,
          0,   0,   0,   0,   0,   0,   0,   0),
    'N': (-66, -53, -75, -75, -10, -55, -58, -70,
          -3,  -6, 100, -36,   4,  62,  -4, -14,
          10,  67,   1,  74,  73,  27,  62,  -2,
          24,  24,  45,  37,  33,  41,  25,  17,
          -1,   5,  31,  21,  22,  35,   2,   0,
          -18,  10,  13,  22,  18,  15,  11, -14,
          -23, -15,   2,   0,   2,   0, -23, -20,
          -74, -23, -26, -24, -19, -35, -22, -69),
    'B': (-59, -78, -82, -76, -23, -107, -37, -50,
          -11,  20,  35, -42, -39,  31,   2, -22,
          -9,  39, -32,  41,  52, -10,  28, -14,
          25,  17,  20,  34,  26,  25,  15,  10,
          13,  10,  17,  23,  17,  16,   0,   7,
          14,  25,  24,  15,   8,  25,  20,  15,
          19,  20,  11,   6,   7,   6,  20,  16,
          -7,   2, -15, -12, -14, -15, -10, -10),
    'R': (35,  29,  33,   4,  37,  33,  56,  50,
          55,  29,  56,  67,  55,  62,  34,  60,
          19,  35,  28,  33,  45,  27,  25,  15,
          0,   5,  16,  13,  18,  -4,  -9,  -6,
          -28, -35, -16, -21, -13, -29, -46, -30,
          -42, -28, -42, -25, -25, -35, -26, -46,
          -53, -38, -31, -26, -29, -43, -44, -53,
          -30, -24, -18,   5,  -2, -18, -31, -32),
    'Q': (6,   1, -8, -104, 69,  24, 88, 26,
          14,  32,  60, -10,  20,  76,  57,  24,
          -2,  43,  32,  60,  72,  63,  43,   2,
          1, -16,  22,  17,  25,  20, -13,  -6,
          -14, -15,  -2,  -5,  -1, -10, -20, -22,
          -30,  -6, -13, -11, -16, -11, -16, -27,
          -36, -18,   0, -19, -15, -15, -21, -38,
          -39, -30, -31, -13, -31, -36, -34, -42),
    'K': (4,  54,  47, -99, -99,  60,  83, -62,
          -32,  10,  55,  56,  56,  55,  10,   3,
          -62,  12, -57,  44, -67,  28,  37, -31,
          -55,  50,  11,  -4, -19,  13,   0, -49,
          -55, -43, -52, -28, -51, -47,  -8, -50,
          -47, -42, -43, -79, -64, -32, -29, -32,
          -4,   3, -14, -50, -57, -18,  13,   4,
          17,  30,  -3, -14,   6,  -1,  40,  18),
}

# fmt: on

for k, table in pst.items():

    def padrow(row):
        return (0,) + tuple(x + piece[k] for x in row) + (0,)

    # fmt: off
    pst[k] = sum((padrow(table[i * 8: i * 8 + 8]) for i in range(8)), ())
    # fmt: on
    pst[k] = (0,) * 20 + pst[k] + (0,) * 20


A1, H1, A8, H8 = 91, 98, 21, 28
initial = (
    "         \n"  # 0 -  9
    "         \n"  # 10 - 19
    " rnbqkbnr\n"  # 20 - 29
    " pppppppp\n"  # 30 - 39
    " ........\n"  # 40 - 49
    " ........\n"  # 50 - 59
    " ........\n"  # 60 - 69
    " ........\n"  # 70 - 79
    " PPPPPPPP\n"  # 80 - 89
    " RNBQKBNR\n"  # 90 - 99
    "         \n"  # 100 -109
    "         \n"  # 110 -119
)

N, E, S, W = -10, 1, 10, -1
directions = {
    "P": (N, N + N, N + W, N + E),
    "N": (
        N + N + E,
        E + N + E,
        E + S + E,
        S + S + E,
        S + S + W,
        W + S + W,
        W + N + W,
        N + N + W,
    ),
    "B": (N + E, S + E, S + W, N + W),
    "R": (N, E, S, W),
    "Q": (N, E, S, W, N + E, S + E, S + W, N + W),
    "K": (N, E, S, W, N + E, S + E, S + W, N + W),
}

MATE_LOWER = piece["K"] - 10 * piece["Q"]
MATE_UPPER = piece["K"] + 10 * piece["Q"]

TABLE_SIZE = 1e7

QS_LIMIT = 219
EVAL_ROUGHNESS = 13
DRAW_TEST = True


class Position(namedtuple("Position", "board score wc bc ep kp")):
    """A state of a chess game.
    board -- a 120 char representation of the board
    score -- the board evaluation
    wc -- the castling rights, [west/queen side, east/king side]
    bc -- the opponent castling rights, [west/king side, east/queen side]
    ep - the en passant square
    kp - the king passant square
    """

    def gen_moves(self):
        for i, p in enumerate(self.board):
            if not p.isupper():
                continue
            for d in directions[p]:
                for j in count(i + d, d):
                    q = self.board[j]
                    if q.isspace() or q.isupper():
                        break
                    if p == "P" and d in (N, N + N) and q != ".":
                        break
                    if (
                        p == "P"
                        and d == N + N
                        and (i < A1 + N or self.board[i + N] != ".")
                    ):
                        break
                    if (
                        p == "P"
                        and d in (N + W, N + E)
                        and q == "."
                        and j not in (self.ep, self.kp, self.kp - 1, self.kp + 1)
                    ):
                        break
                    yield (i, j)
                    if p in "PNK" or q.islower():
                        break
                    if i == A1 and self.board[j + E] == "K" and self.wc[0]:
                        yield (j + E, j + W)
                    if i == H1 and self.board[j + W] == "K" and self.wc[1]:
                        yield (j + W, j + E)

    def rotate(self):
        """Rotates the board, preserving enpassant."""
        return Position(
            self.board[::-1].swapcase(),
            -self.score,
            self.bc,
            self.wc,
            119 - self.ep or 0,
            119 - self.kp or 0,
        )

    def nullmove(self):
        """Like rotate, but clears ep and kp."""
        return Position(
            self.board[::-1].swapcase(), -self.score, self.bc, self.wc, 0, 0
        )

    def move(self, move):
        i, j = move
        p = self.board[i]

        def put(board, i, p):
            # fmt: off
            return board[:i] + p + board[i + 1:]
            # fmt: on

        board = self.board
        wc, bc, ep, kp = self.wc, self.bc, 0, 0
        score = self.score + self.value(move)

        board = put(board, j, board[i])
        board = put(board, i, ".")

        if i == A1:
            wc = (False, wc[1])
        if i == H1:
            wc = (wc[0], False)
        if j == A8:
            bc = (bc[0], False)
        if j == H8:
            bc = (False, bc[1])

        if p == "K":
            wc = (False, False)
            if abs(j - i) == 2:
                kp = (i + j) // 2
                board = put(board, A1 if j < i else H1, ".")
                board = put(board, kp, "R")

        if p == "P":
            if A8 <= j <= H8:
                board = put(board, j, "Q")
            if j - i == 2 * N:
                ep = i + N
            if j == self.ep:
                board = put(board, j + S, ".")

        return Position(board, score, wc, bc, ep, kp).rotate()

    def value(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]

        score = pst[p][j] - pst[p][i]

        if q.islower():
            score += pst[q.upper()][119 - j]

        if abs(j - self.kp) < 2:
            score += pst["K"][119 - j]

        if p == "K" and abs(i - j) == 2:
            score += pst["R"][(i + j) // 2]
            score -= pst["R"][A1 if j < i else H1]

        if p == "P":
            if A8 <= j <= H8:
                score += pst["Q"][j] - pst["P"][j]
            if j == self.ep:
                score += pst["P"][119 - (j + S)]
        return score


Entry = namedtuple("Entry", "lower upper")


class Searcher:
    def __init__(self):
        self.tp_score = {}
        self.tp_move = {}
        self.history = set()
        self.nodes = 0

    def bound(self, pos, gamma, depth, root=True):
        """Returns r where.
        s(pos) <= r < gamma    if gamma > s(pos)
        gamma <= r <= s(pos)   if gamma <= s(pos)
        """
        self.nodes += 1

        depth = max(depth, 0)

        if pos.score <= -MATE_LOWER:
            return -MATE_UPPER

        if DRAW_TEST and not root and pos in self.history:
            return 0

        entry = self.tp_score.get((pos, depth, root), Entry(-MATE_UPPER, MATE_UPPER))
        if entry.lower >= gamma and (not root or self.tp_move.get(pos) is not None):
            return entry.lower
        if entry.upper < gamma:
            return entry.upper

        def moves():

            if depth > 0 and not root and any(c in pos.board for c in "RBNQ"):
                yield None, -self.bound(
                    pos.nullmove(), 1 - gamma, depth - 3, root=False
                )

            if depth == 0:
                yield None, pos.score

            killer = self.tp_move.get(pos)
            if killer and (depth > 0 or pos.value(killer) >= QS_LIMIT):
                yield killer, -self.bound(
                    pos.move(killer), 1 - gamma, depth - 1, root=False
                )

            for move in sorted(pos.gen_moves(), key=pos.value, reverse=True):

                if depth > 0 or pos.value(move) >= QS_LIMIT:
                    yield move, -self.bound(
                        pos.move(move), 1 - gamma, depth - 1, root=False
                    )

        best = -MATE_UPPER
        for move, score in moves():
            best = max(best, score)
            if best >= gamma:
                if len(self.tp_move) > TABLE_SIZE:
                    self.tp_move.clear()
                self.tp_move[pos] = move
                break

        if best < gamma and best < 0 and depth > 0:

            def is_dead(pos):
                return any(pos.value(m) >= MATE_LOWER for m in pos.gen_moves())

            if all(is_dead(pos.move(m)) for m in pos.gen_moves()):
                in_check = is_dead(pos.nullmove())
                best = -MATE_UPPER if in_check else 0

        if len(self.tp_score) > TABLE_SIZE:
            self.tp_score.clear()

        if best >= gamma:
            self.tp_score[pos, depth, root] = Entry(best, entry.upper)
        if best < gamma:
            self.tp_score[pos, depth, root] = Entry(entry.lower, best)

        return best

    def search(self, pos, history=()):
        """Iterative deepening MTD-bi search."""
        self.nodes = 0
        if DRAW_TEST:
            self.history = set(history)
            self.tp_score.clear()

        for depth in range(1, 1000):
            lower, upper = -MATE_UPPER, MATE_UPPER
            while lower < upper - EVAL_ROUGHNESS:
                gamma = (lower + upper + 1) // 2
                score = self.bound(pos, gamma, depth)
                if score >= gamma:
                    lower = score
                if score < gamma:
                    upper = score

            self.bound(pos, lower, depth)

            yield depth, self.tp_move.get(pos), self.tp_score.get(
                (pos, depth, True)
            ).lower


def parse(c):
    fil, rank = ord(c[0]) - ord("a"), int(c[1]) - 1
    return A1 + fil - 10 * rank


def render(i):
    rank, fil = divmod(i - A1, 10)
    return chr(fil + ord("a")) + str(-rank + 1)


async def print_pos(ctx, pos):
    uni_pieces = {
        "r": "♜",
        "n": "♞",
        "b": "♝",
        "q": "♛",
        "k": "♚",
        "p": "♟",
        "R": "♖",
        "N": "♘",
        "B": "♗",
        "Q": "♕",
        "K": "♔",
        "P": "♙",
        ".": "\u2004\u2004\u2005",
    }
    msg = ""
    for i, row in enumerate(pos.board.split()):
        msg += f"{''.join(uni_pieces.get(p, p) for p in row)}\n"

    background = Image.open("fonts/chess.png")
    img = Image.new("RGBA", (1024, 1050), (255, 0, 0, 0))

    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("fonts/DejaVuSans.ttf", 135)
    d.text((40, 0), msg, font=font, fill=(0, 0, 0), spacing=4)
    background.paste(img, (0, 0), img)

    with io.BytesIO() as image_binary:
        background.save(image_binary, "PNG")
        image_binary.seek(0)
        return await ctx.send(file=discord.File(fp=image_binary, filename="image.png"))


class chess(commands.Cog):
    """For commands related to the chess bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.is_running = False

    @staticmethod
    def cog_unload():
        DB.db.delete(b"playing_chess")

    @commands.command(hidden=True)
    async def chess(self, ctx):
        """Starts a game of chess against an bot."""
        if self.is_running is True:
            return await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="```A game is already running```",
                )
            )

        self.is_running = True

        # To stop logging of messages while playing chess cause it is spamy
        DB.db.put(b"playing_chess", str(ctx.author.id).encode())

        embed = discord.Embed(color=discord.Color.blurple())
        chess_message = None

        hist = [Position(initial, 0, (True, True), (True, True), 0, 0)]
        searcher = Searcher()

        def check(message: discord.Message) -> bool:
            return message.author.id == ctx.author.id and message.channel == ctx.channel

        while True:
            if chess_message:
                await chess_message.delete()
            chess_message = await print_pos(ctx, hist[-1])

            if hist[-1].score <= -MATE_LOWER:
                embed.title = "You lost"
                return await ctx.send(embed=embed)

            move = None
            while move not in hist[-1].gen_moves():
                if move is not None:
                    embed.title = "Enter a move like e2e4 or surrender"
                    await ctx.send(embed=embed)

                try:
                    message = await ctx.bot.wait_for(
                        "message", timeout=300.0, check=check
                    )
                except asyncio.TimeoutError:
                    self.is_running = False
                    DB.db.delete(b"playing_chess")
                    embed.title = "Game timed out"
                    return await ctx.send(embed=embed)

                if "surrender" in message.content.lower():
                    await message.delete()
                    return await chess_message.add_reaction("❌")

                match = re.match("([a-h][1-8])" * 2, message.content.lower())
                if match:
                    move = parse(match.group(1)), parse(match.group(2))
                else:
                    embed.title = "Enter a move like e2e4 or surrender"
                    await ctx.send(embed=embed)
            await message.delete()

            hist.append(hist[-1].move(move))

            if hist[-1].score <= -MATE_LOWER:
                embed.title = "You won"
                return await ctx.send(embed=embed)

            start = time.time()
            for _depth, move, score in searcher.search(hist[-1], hist):
                if time.time() - start > 0.3:
                    if score == MATE_UPPER:
                        embed.title = "Checkmate!"
                        return await ctx.send(embed=embed)
                    break

            hist.append(hist[-1].move(move))
        self.is_running = False
        DB.db.delete(b"playing_chess")


def setup(bot: commands.Bot) -> None:
    """Starts the chess cog."""
    DB.db.delete(b"playing_chess")
    bot.add_cog(chess(bot))
