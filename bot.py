import os
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1484657223216009297

bot = discord.Bot()


# =========================================================
# BOTÃO DO PAINEL
# =========================================================

class PainelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="RESGATAR PAINEL GRÁTIS!",
        emoji="🎁",
        style=discord.ButtonStyle.green,
        custom_id="painel_resgatar"
    )
    async def resgatar(
        self,
        button,
        interaction: discord.Interaction
    ):
        await interaction.response.send_modal(ResgateModal())


# =========================================================
# MODAL
# =========================================================

class ResgateModal(discord.ui.DesignerModal):

    def __init__(self):

        self.missao = discord.ui.Select(
            custom_id="missao",
            placeholder="Selecione Sim ou Não",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Sim, já fiz",
                    description="Já completei e tenho o print.",
                    value="sim"
                ),
                discord.SelectOption(
                    label="Não, ainda não",
                    description="Ainda não fiz a missão.",
                    value="nao"
                )
            ]
        )

        self.print_missao = discord.ui.FileUpload(
            custom_id="print_missao",
            min_values=1,
            max_values=1
        )

        self.plataforma = discord.ui.Select(
            custom_id="plataforma",
            placeholder="Escolha a plataforma",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Android",
                    description="Key para Android",
                    value="android"
                ),
                discord.SelectOption(
                    label="iOS",
                    description="Key para iOS",
                    value="ios"
                ),
                discord.SelectOption(
                    label="PC",
                    description="Key para emulador / PC",
                    value="pc"
                )
            ]
        )

        super().__init__(
            discord.ui.Label(
                "VOCÊ FEZ A MISSÃO?",
                self.missao,
                description="Selecione Sim ou Não"
            ),

            discord.ui.Label(
                "Print da missão",
                self.print_missao,
                description="Apenas 1 imagem PNG/JPG."
            ),

            discord.ui.Label(
                "Plataforma",
                self.plataforma,
                description="Para qual dispositivo você quer a key"
            ),

            title="Resgatar Painel Grátis"
        )

    async def callback(self, interaction: discord.Interaction):

        missao = self.missao.values[0]

        # =============================================
        # NÃO FEZ
        # =============================================

        if missao == "nao":

            await interaction.response.send_message(
                "❌ **Você ainda não fez a missão!**\n\n"
                "Complete a missão primeiro e depois "
                "clique novamente em **Resgatar Painel Grátis**.",
                ephemeral=True
            )

            return

        # =============================================
        # PEGAR ARQUIVO
        # =============================================

        arquivos = self.print_missao.values

        if not arquivos:

            await interaction.response.send_message(
                "❌ Você precisa enviar o print da missão.",
                ephemeral=True
            )

            return

        arquivo = arquivos[0]

        # =============================================
        # VERIFICAR IMAGEM
        # =============================================

        tipo = arquivo.content_type or ""

        if not tipo.startswith("image/"):

            await interaction.response.send_message(
                "❌ O arquivo precisa ser uma imagem PNG ou JPG.",
                ephemeral=True
            )

            return

        # =============================================
        # PLATAFORMA
        # =============================================

        plataforma = self.plataforma.values[0]

        nomes = {
            "android": "Android",
            "ios": "iOS",
            "pc": "PC / Emulador"
        }

        plataforma_nome = nomes.get(
            plataforma,
            plataforma
        )

        guild = interaction.guild

        if guild is None:
            return

        # =============================================
        # EVITAR DOIS TICKETS
        # =============================================

        for canal in guild.text_channels:

            if canal.topic == f"resgate:{interaction.user.id}":

                await interaction.response.send_message(
                    f"⚠️ Você já possui um resgate aberto: "
                    f"{canal.mention}",
                    ephemeral=True
                )

                return

        # =============================================
        # PERMISSÕES
        # =============================================

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True
                )
        }

        # =============================================
        # CRIAR CANAL
        # =============================================

        canal = await guild.create_text_channel(
            name=f"resgate-{interaction.user.name}",
            overwrites=overwrites,
            topic=f"resgate:{interaction.user.id}"
        )

        # =============================================
        # EMBED
        # =============================================

        embed = discord.Embed(
            title="🎁 NOVO RESGATE",
            description=(
                f"👤 **Usuário:** {interaction.user.mention}\n\n"
                f"📱 **Plataforma:** `{plataforma_nome}`\n\n"
                "📸 **Print da missão:**\n"
                "O comprovante está abaixo.\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "🟢 **APROVAR**\n"
                "Aprova o pedido e mantém o canal aberto "
                "para a equipe enviar a Key manualmente.\n\n"
                "🔴 **REPROVAR**\n"
                "Reprova e fecha o canal.\n\n"
                "🔒 **FECHAR CANAL**\n"
                "Fecha o canal."
            ),
            color=discord.Color.blurple()
        )

        embed.set_image(url=arquivo.url)

        embed.set_footer(
            text="Sistema de Resgate • Painel Grátis"
        )

        await canal.send(
            content=interaction.user.mention,
            embed=embed,
            view=TicketView()
        )

        # =============================================
        # RESPOSTA
        # =============================================

        await interaction.response.send_message(
            f"✅ **Resgate enviado!**\n\n"
            f"Seu atendimento foi criado em {canal.mention}",
            ephemeral=True
        )


# =========================================================
# BOTÕES DO TICKET
# =========================================================

class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    # =====================================================
    # APROVAR
    # =====================================================

    @discord.ui.button(
        label="APROVAR",
        emoji="✅",
        style=discord.ButtonStyle.green,
        custom_id="ticket_aprovar"
    )
    async def aprovar(self, button, interaction):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Você não tem permissão.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ **RESGATE APROVADO!**\n\n"
            "O canal continua aberto.\n"
            "Envie a Key manualmente neste canal."
        )

    # =====================================================
    # REPROVAR
    # =====================================================

    @discord.ui.button(
        label="REPROVAR",
        emoji="❌",
        style=discord.ButtonStyle.red,
        custom_id="ticket_reprovar"
    )
    async def reprovar(self, button, interaction):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Você não tem permissão.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "❌ Resgate reprovado. Fechando canal..."
        )

        await interaction.channel.delete()

    # =====================================================
    # FECHAR
    # =====================================================

    @discord.ui.button(
        label="FECHAR CANAL",
        emoji="🔒",
        style=discord.ButtonStyle.gray,
        custom_id="ticket_fechar"
    )
    async def fechar(self, button, interaction):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Você não tem permissão.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🔒 Fechando canal..."
        )

        await interaction.channel.delete()


# =========================================================
# /PAINEL
# =========================================================

@bot.slash_command(
    name="painel",
    description="Envia o painel de resgate",
    guild_ids=[GUILD_ID]
)
async def painel(ctx):

    if not ctx.author.guild_permissions.administrator:

        await ctx.respond(
            "❌ Você precisa ser administrador.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="🎁 PAINEL 100% GRÁTIS!",
        description=(
            "**COMO FAZER A MISSÃO?**\n\n"
            "1️⃣ Faça a missão solicitada.\n\n"
            "2️⃣ Quando terminar, tire um print "
            "comprovando a missão.\n\n"
            "3️⃣ Clique no botão abaixo e envie "
            "seu comprovante.\n\n"
            "🎁 **Resgate seu painel grátis!**"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text="Painel Grátis"
    )

    await ctx.respond(
        "✅ Painel enviado!",
        ephemeral=True
    )

    await ctx.channel.send(
        embed=embed,
        view=PainelView()
    )


# =========================================================
# INICIAR
# =========================================================

@bot.event
async def on_ready():

    print("━━━━━━━━━━━━━━━━━━━━")
    print("🤖 BOT ONLINE")
    print(f"👤 {bot.user}")
    print(f"🆔 Guild: {GUILD_ID}")
    print("━━━━━━━━━━━━━━━━━━━━")

    bot.add_view(PainelView())
    bot.add_view(TicketView())


# =========================================================
# TOKEN
# =========================================================

if not TOKEN:

    print("❌ DISCORD_TOKEN não encontrado!")

else:

    bot.run(TOKEN)
