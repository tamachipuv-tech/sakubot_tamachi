import discord
from discord.ext import commands
import os
import random
from discord import option
from flask import Flask
import threading    
from threading import Thread

TOKEN = os.environ['DISCORD_TOKEN']  # ReplitのSecretsに設定してね

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class RecruitmentView(discord.ui.View):
    def __init__(self, author, game, max_participants, timeout=300):
        super().__init__(timeout=timeout)
        self.author = author
        self.game = game
        self.max_participants = max_participants
        self.participants = []

    @discord.ui.button(label="✅ 参加", style=discord.ButtonStyle.success)
    async def join(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user
        if user in self.participants:
            await interaction.response.send_message("すでに参加しています！", ephemeral=True)
        elif len(self.participants) >= self.max_participants:
            await interaction.response.send_message("定員に達しています。", ephemeral=True)
        else:
            self.participants.append(user)
            await interaction.response.send_message(f"{user.mention} が参加しました！（{len(self.participants)}/{self.max_participants}）", ephemeral=False)

    @discord.ui.button(label="🛑 取り消し", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("この募集を取り消せるのは作成者だけです。", ephemeral=True)
        else:
            await interaction.message.edit(content="❌ 募集は取り消されました。", embed=None, view=None)
            self.stop()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.slash_command(name="募集", description="ゲームの募集を開始します")
async def 募集(ctx, ゲーム: str, 時間: str, 募集人数: int):
    embed = discord.Embed(
        title=f"{ゲーム} の募集",
        description=(
            f"{ctx.author.mention} が {時間} に {ゲーム} を一緒に遊ぶ人を募集しています！\n"
            f"定員: {募集人数}人\n\n"
            f"下のボタンで参加／取り消しができます。"
        ),
        color=discord.Color.green()
    )

    view = RecruitmentView(author=ctx.author, game=ゲーム, max_participants=募集人数)
    await ctx.respond(embed=embed, view=view)

BOT_ADMIN_IDS = [1398653546563375167]  # 自分のDiscordユーザーIDに変更してね

@bot.slash_command(name="botrestart", description="BOTを再起動します（すべてのサーバーに通知）")
async def botrestart(ctx):
                    if ctx.author.id not in BOT_ADMIN_IDS:
                        await ctx.respond("❌ このコマンドはBOT管理者のみが使用できます。", ephemeral=True)
                        return

                    await ctx.respond("🛰️ すべてのサーバーに再起動通知を送信します。")

                    message = "🔁 このBOTはまもなく再起動されます。しばらくお待ちください。ゲーム募集・投票はすべて無効になりますので、ご注意ください。"

                    for guild in bot.guilds:
                        # まずはシステムチャンネルを使う（BOTが送信できる場合）
                        channel = guild.system_channel
                        if channel and channel.permissions_for(guild.me).send_messages:
                            await channel.send(message)
                            continue

                        # システムチャンネルがダメなら、送信可能なテキストチャンネルを探す
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                await ch.send(message)
                                break

@bot.slash_command(name="report", description="ユーザーを通報します（モデレーターに送信されます）")
async def report(ctx, 通報対象: discord.Member, 理由: str):
    await ctx.respond("📨 通報を受け付けました。対応までしばらくお待ちください。", ephemeral=True)

    # 通報先のチャンネルID（モデレーター用）
    REPORT_CHANNEL_ID = 1427605885747724339  # ← 通報を受け取るチャンネルのIDに変えてね

    report_channel = bot.get_channel(REPORT_CHANNEL_ID)
    if report_channel:
        embed = discord.Embed(
            title="🚨 通報がありました",
            description=(
                f"**通報者**: {ctx.author.mention}\n"
                f"**対象**: {通報対象.mention} (`{通報対象.id}`)\n"
                f"**理由**: {理由}"
            ),
            color=discord.Color.red()
        )
        await report_channel.send(embed=embed)

# お題のリスト（自分で増やしてOK）
OGIRI_PROMPTS = [
    "こんなマイクラの実績は嫌だ。どんな実績？",
    "クリーパーの意外な悩みとは？",
    "エンダードラゴンが実は○○だった！？",
    "「村人が急に話し始めた！」最初に言った一言とは？",
    "マイクラの世界に〇〇が導入されたらどうなる？",
    "水バケツ着地しようとしたら水が消えた、なぜ消えた?",
]

@bot.slash_command(name="大喜利", description="大喜利のお題を出します")
async def ogiri(ctx):
    prompt = random.choice(OGIRI_PROMPTS)
    await ctx.respond(f"🗯️ **お題：** {prompt}")

@bot.slash_command(name="サーバー情報", description="このサーバーの情報を表示します")
async def サーバー情報(ctx):
    guild = ctx.guild

    name = guild.name
    owner = guild.owner or "取得できません"
    roles = len(guild.roles)
    created_at = guild.created_at.strftime("%Y年%m月%d日 %H:%M")
    member_count = guild.member_count

    embed = discord.Embed(title="📊 サーバー情報", color=discord.Color.blurple())
    embed.add_field(name="サーバー名", value=name, inline=False)

    # オーナーの mention を安全に表示（取得できなければ文字だけ）
    if isinstance(owner, discord.Member):
        embed.add_field(name="オーナー", value=owner.mention, inline=False)
    else:
        embed.add_field(name="オーナー", value=str(owner), inline=False)

    embed.add_field(name="ロール数", value=f"{roles} 個", inline=False)
    embed.add_field(name="作成日", value=created_at, inline=False)
    embed.add_field(name="参加人数", value=f"{member_count} 人", inline=False)

    await ctx.respond(embed=embed)

@bot.slash_command(name="お題申請", description="大喜利のお題を申請します（モデレーターに送信されます）")
async def お題申請(ctx, お題: str):
            await ctx.respond("📨 お題の申請を受け付けました！確認まで少々お待ちください。", ephemeral=True)

            # モデレーター用の送信先チャンネル ID（書き換えて！）
            MOD_CHANNEL_ID = 1419270020420341915

            mod_channel = bot.get_channel(MOD_CHANNEL_ID)
            if mod_channel:
                embed = discord.Embed(
                    title="📝 お題の追加申請",
                    description=(
                        f"**申請者**: {ctx.author.mention} (`{ctx.author.id}`)\n"
                        f"**申請お題**:\n{お題}"
                    ),
                    color=discord.Color.orange()
                )
                await mod_channel.send(embed=embed)

DAILY_MISSIONS = [
    "クリーパーを爆発させずに倒せ",
    "原木を64個集めよ",
    "水バケツで落下死を回避せよ",
    "馬に乗って1000ブロック移動せよ",
    "ネザーで10分生き延びろ"
]

@bot.slash_command(name="ミッション", description="今日のミッションを受け取ります")
async def ミッション(ctx):
    mission = random.choice(DAILY_MISSIONS)
    await ctx.respond(f"🎯 今日のミッション：\n**{mission}**")

class VoteView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.votes = {opt: 0 for opt in options}
        self.options = options
        self.message = None

        for opt in options:
            self.add_item(VoteButton(opt, self))

    async def update_message(self):
        description = "\n".join([f"**{opt}**: {count}票" for opt, count in self.votes.items()])
        embed = discord.Embed(title="🗳️ 投票中", description=description, color=discord.Color.blurple())
        if self.message:
            await self.message.edit(embed=embed, view=self)

class VoteButton(discord.ui.Button):
    def __init__(self, label, view):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.view_obj = view

    async def callback(self, interaction: discord.Interaction):
        self.view_obj.votes[self.label] += 1
        await interaction.response.send_message(f"✅ {interaction.user.mention} が **{self.label}** に投票しました！", ephemeral=True)
        await self.view_obj.update_message()


@bot.slash_command(name="投票", description="シンプルな投票を作成します")
@option("お題", description="投票のお題")
@option("選択肢1", description="1つ目の選択肢")
@option("選択肢2", description="2つ目の選択肢")
async def 投票(ctx: discord.ApplicationContext, お題: str, 選択肢1: str, 選択肢2: str):
    options = [選択肢1, 選択肢2]

    view = VoteView(options)
    embed = discord.Embed(
        title=f"🗳️ 投票：{お題}",
        description="\n".join([f"**{opt}**: 0票" for opt in options]),
        color=discord.Color.blurple()
    )
    message = await ctx.respond(embed=embed, view=view)
    view.message = await message.original_response()

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(TOKEN)
