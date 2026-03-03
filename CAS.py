import discord
from discord.ext import commands
import os

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

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= Buttons =================
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim",
                       style=discord.ButtonStyle.primary,
                       custom_id="ticket_claim_button")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        thread = interaction.channel
        topic = thread.topic or ""

        if "claimed_by=" in topic:
            claimed_id = topic.split("claimed_by=")[1].split()[0]
            return await interaction.response.send_message(
                f"❌ Ticket already claimed by <@{claimed_id}>",
                ephemeral=True
            )

        await thread.edit(topic=f"{topic} claimed_by={interaction.user.id}".strip())

        button.label = f"Claimed by {interaction.user.display_name}"
        button.style = discord.ButtonStyle.success
        button.disabled = True

        await interaction.response.edit_message(view=self)
        await thread.send(f"📌 Ticket claimed by {interaction.user.mention}")

    @discord.ui.button(label="Unclaim",
                       style=discord.ButtonStyle.secondary,
                       custom_id="ticket_unclaim_button")
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        thread = interaction.channel
        topic = thread.topic or ""

        if not interaction.user.guild_permissions.manage_threads:
            return await interaction.response.send_message(
                "❌ You don't have permission",
                ephemeral=True
            )

        if "claimed_by=" not in topic:
            return await interaction.response.send_message(
                "❌ Ticket is not claimed",
                ephemeral=True
            )

        new_topic = topic.split("claimed_by=")[0].strip()
        await thread.edit(topic=new_topic)

        for item in self.children:
            if item.custom_id == "ticket_claim_button":
                item.label = "Claim"
                item.style = discord.ButtonStyle.primary
                item.disabled = False

        await interaction.response.edit_message(view=self)
        await thread.send(f"🔓 Ticket unclaimed by {interaction.user.mention}")

    @discord.ui.button(label="Close",
                       style=discord.ButtonStyle.danger,
                       custom_id="ticket_close_button")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Ticket closed", ephemeral=True)
        await interaction.channel.edit(archived=True)

# ================= Select =================
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

        super().__init__(
            placeholder="Choose a category",
            options=options,
            custom_id="ticket_category_select"
        )

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        category = self.values[0]
        guild = interaction.guild
        member = interaction.user

        channel = guild.get_channel(CATEGORY_CHANNELS.get(category))
        if not channel:
            return await interaction.followup.send(
                "❌ Category channel not found",
                ephemeral=True
            )

        # ===== Counter System =====
        topic = channel.topic or ""
        counter = 0

        if "ticket_counter=" in topic:
            try:
                counter = int(topic.split("ticket_counter=")[1].split()[0])
            except:
                counter = 0

        default_starts = {
            "valorant": 22,
            "lol": 66,
            "marvel": 15,
            "shop": 0
        }

        if counter == 0:
            counter = default_starts.get(category, 0)

        counter += 1

        await channel.edit(topic=f"ticket_counter={counter}")

        number = str(counter).zfill(3)
        thread_name = f"{category}-{number}"

        # ===== Create Thread =====
        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            auto_archive_duration=1440
        )

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"{member.mention} opened **{category}** ticket\nTicket ID: {number}",
            color=discord.Color.purple()
        )

        await thread.send(
            content=f"{member.mention} <@&{SUPPORT_ROLE_ID}> <@&{EXTRA_ROLE_ID}>",
            embed=embed,
            view=TicketButtons()
        )

        # ===== Ephemeral Message =====
        await interaction.followup.send(
            f"✅ Your ticket has been created: {thread.mention}",
            ephemeral=True
        )

        # ===== Reset Select =====
        self.values = []
        await interaction.message.edit(view=self.view)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.command()
async def CAS(ctx):
    await ctx.send("👇 اختار الخدمة اللي انت عايزها", view=TicketView())

@bot.event
async def on_ready():
    bot.add_view(TicketButtons())
    bot.add_view(TicketView())
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
