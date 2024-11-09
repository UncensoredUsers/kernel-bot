import discord
from discord.ext import commands

# 봇을 초기화하고 Intents 설정
intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용 접근 권한
intents.guilds = True
intents.dm_messages = True  # DM 메시지에 대한 접근 권한

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_CHANNEL_ID = 1304769645848563783

# 봇 준비 완료 이벤트
@bot.event
async def on_ready():
    await bot.sync_commands()
    activity = discord.Activity(type=discord.ActivityType.playing, name="서버를 관리")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    # 봇 자신의 메시지와 서버 메시지는 무시
    if message.author == bot.user or message.guild is not None:
        return

    # DM에서 온 메시지라면, 특정 채널에 전송
    if isinstance(message.channel, discord.DMChannel):
        # 임베드 생성
        embed = discord.Embed(title="새로운 문의가 도착했습니다.", description=message.content, color=discord.Color.blue())
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        embed.set_footer(text="Kernel Bot")

        # 지정된 서버 채널에 임베드 전송
        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        if target_channel:
            await target_channel.send(embed=embed)

        # 사용자에게 임베드 형식으로 확인 메시지 전송
        confirmation_embed = discord.Embed(
            title="문의가 전송되었습니다.",
            description=f"문의가 접수되었습니다. 처리까지 최대 24시간이 소요됩니다.\n\n**전송된 메세지:**\n{message.content}",
            color=discord.Color.green()
        )
        confirmation_embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        confirmation_embed.set_footer(text="Kernel Bot")
        
        try:
            await message.author.send(embed=confirmation_embed)
        except discord.errors.Forbidden:
            print(f"{message.author.name}에게 DM을 보낼 수 없습니다. DM이 꺼져있을수 있습니다.")

    # 명령어 인식을 위해 메시지 처리 계속
    await bot.process_commands(message)

# ping 슬래시 명령어
@bot.slash_command(name="핑", description="봇의 핑을 확인합니다.")
async def ping(ctx: discord.ApplicationContext):
    latency = round(bot.latency * 1000)  # 밀리초 단위로 변환
    await ctx.respond(f"퐁! 🏓 \n핑: {latency}ms")

@bot.slash_command(name="공지", description="특정채널에 공지를 보냅니다.")
async def announce(
    ctx: discord.ApplicationContext, 
    channel: discord.TextChannel, 
    title: str, 
    description: str
):
    # 관리자 권한 확인
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return

    # 임베드 생성
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    embed.set_footer(text="Kernel Bot")  # Footer 설정

    # 공지 채널에 임베드 전송
    await channel.send(embed=embed)
    await ctx.respond(f"{channel.mention} 채널에 성공적으로 메세지를 전송하였습니다.", ephemeral=True)

# DM을 보내는 명령어 추가 (멘션 유저로 DM 보내기)
@bot.slash_command(name="DM보내기", description="특정 사용자에게 DM을 보냅니다.")
async def send_dm(
    ctx: discord.ApplicationContext,
    user: discord.User,  # 멘션된 유저
    title: str,  # 임베드 제목
    description: str  # 임베드 설명
):
    # 관리자 권한 확인
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return

    try:
        # 멘션된 유저에게 DM 전송
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        embed.set_footer(text="Kernel Bot")

        # 해당 유저에게 DM 전송
        await user.send(embed=embed)
        await ctx.respond(f"{user.mention}에게 DM이 성공적으로 전송되었습니다.", ephemeral=True)
    except discord.errors.Forbidden:
        await ctx.respond(f"{user.mention}에게 DM을 보낼 수 없습니다. DM이 꺼져있을 수 있습니다.", ephemeral=True)
    except discord.errors.NotFound:
        await ctx.respond(f"{user.mention}을 찾을 수 없습니다.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"DM 전송 중 오류가 발생했습니다: {e}", ephemeral=True)

# 전체 유저에게 DM을 보내는 명령어 추가
@bot.slash_command(name="모든유저에게dm", description="서버의 모든 사용자에게 DM을 보냅니다.")
async def send_dm_all(
    ctx: discord.ApplicationContext,
    title: str,  # 임베드 제목
    description: str  # 임베드 설명
):
    # 관리자 권한 확인
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return

    # 모든 멤버에게 DM 전송
    guild = ctx.guild  # 현재 서버 객체
    failed_users = []  # DM 실패한 유저 목록

    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    embed.set_footer(text="Kernel Bot")

    for member in guild.members:
        try:
            if member.bot:  # 봇에게는 DM을 보내지 않음
                continue
            await member.send(embed=embed)
        except discord.errors.Forbidden:
            failed_users.append(member.name)  # DM 실패한 유저 추가
        except Exception as e:
            print(f"DM 전송 중 오류 발생: {e}")

    if failed_users:
        failed_user_list = "\n".join(failed_users)
        await ctx.respond(f"DM 전송 실패한 유저: {failed_user_list}", ephemeral=True)
    else:
        await ctx.respond("모든 유저에게 DM이 성공적으로 전송되었습니다.", ephemeral=True)

# 봇 실행
bot.run("token")
