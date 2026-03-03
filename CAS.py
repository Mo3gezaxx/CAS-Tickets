import discord
from discord.ext import commands
import json
import os

# ===== ENV (Railway) =====
TOKEN = os.getenv("TOKEN")

SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID"))
EXTRA_ROLE_ID = int(os.getenv("EXTRA_ROLE_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

CATEGORY_CHANNELS = {
    "shop": int(os.getenv("SHOP_CHANNEL_ID")),
    "lol": int(os.getenv("LOL_CHANNEL_ID")),
    "valorant": int(os.getenv("VALORANT_CHANNEL_ID")),
    "marvel": int(os.getenv("MARVEL_CHANNEL_ID")),
}

# ===== Ticket Descriptions =====
TICKET_DESCRIPTIONS = {
    "lol": """اهم حاجه خلي الاكونت اسمو نفس اليوزر اللى هبعتهولك
و اللعب ارام بس 
و لو عايز تلعب مع حد من اصحابك عادي بس قبل متسلمني تعملهم unfriend 
بلاش تبقى توكسيك ولو لقيت نفسك هتكون افك اكتب فى الروم <#1475111804232405023> و منشن رول levelers
ولو فى اي حاجه مش فاهمها او هتعك فيها او عكتها بالفعل قولي متتكسفش يمكن نعرف نحلها سوا <#1475099936692637756>
و حاول تدي التيم بتاعك اونر حتي لو كان مش احسن حاجه""",

    "valorant": "",
    "shop": "",
    "marvel": ""
}

# ===== Counter File =====
COUNTER_FILE = "tickets.json"

if os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "r") as f:
        ticket_counters = json.load(f)
else:
    ticket_counters = {"shop": 0, "lol": 0, "valorant": 0, "marvel": 0}


def save_counters():
    with open(COUNTER_FILE, "w") as f:
        json.dump(ticket_counters, f)


# ===== Bot =====
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ===== Buttons =====
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"📌 Claimed by {interaction.user.mention}",
            ephemeral=True
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = interaction.channel
        guild = interaction.guild
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        opener = thread.owner_id
        closer = interaction.user

        # ===== Log Embed =====
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            color=discord.Color.green()
        )
        embed.add_field(name="Ticket", value=thread.name)
        embed.add_field(name="Opened By", value=f"<@{opener}>")
        embed.add_field(name="Closed By", value=closer.mention)
        embed.add_field(
            name="Time",
            value=discord.utils.format_dt(discord.utils.utcnow())
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="View Thread", url=thread.jump_url))

        if log_channel:
            await log_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "✅ Ticket closed",
            ephemeral=True
        )

        # ===== Archive =====
        await thread.edit(archived=True)


# ===== Select =====
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Buy From Our Shop",
                value="shop",
                emoji=discord.PartialEmoji(name="shop", id=1475214748021948456)
            ),
            discord.SelectOption(
                label="League of Legends",
                value="lol",
                emoji=discord.PartialEmoji(name="lol", id=1475214617511723128)
            ),
            discord.SelectOption(
                label="Valorant",
                value="valorant",
                emoji=discord.PartialEmoji(name="valorant", id=1433440387074232330)
            ),
            discord.SelectOption(
                label="Marvel Rivals",
                value="marvel",
                emoji=discord.PartialEmoji(name="marvel", id=1475216899141795954)
            ),
        ]
        super().__init__(placeholder="Choose a category", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        category = self.values[0]
        guild = interaction.guild
        member = interaction.user

        channel_id = CATEGORY_CHANNELS.get(category)
        channel = guild.get_channel(channel_id)

        if not channel:
            return await interaction.followup.send(
                "❌ Category channel not found",
                ephemeral=True
            )

        # ===== Counter =====
        ticket_counters[category] += 1
        save_counters()

        number = str(ticket_counters[category]).zfill(3)
        thread_name = f"{category}-{number}"

        # ===== Create Thread =====
        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            auto_archive_duration=1440
        )

        # ===== Embed =====
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"{member.mention} opened **{category}** ticket",
            color=discord.Color.purple()
        )

        description_text = TICKET_DESCRIPTIONS.get(category)
        if description_text:
            embed.add_field(
                name="📋 Instructions",
                value=description_text,
                inline=False
            )

        # ===== Send Ticket Message =====
        await thread.send(
            content=f"{member.mention} <@&{SUPPORT_ROLE_ID}> <@&{EXTRA_ROLE_ID}>",
            embed=embed,
            view=TicketButtons()
        )

        await interaction.followup.send(
            f"✅ Ticket created: {thread.mention}",
            ephemeral=True
        )

        # Reset select
        await interaction.message.edit(view=TicketView())


# ===== Panel =====
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


@bot.command()
async def CAS(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Admin only")

    await ctx.send(
        "اختار الخدمة اللي انت عايزها 👇",
        view=TicketView()
    )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


bot.run(TOKEN)
