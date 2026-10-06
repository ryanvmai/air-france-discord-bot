import os
import re
import json
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

VERSION = "0.1.0"
BUILD = 8

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# LOAD AIR FRANCE FLEET
# ============================================================

with open("fleet.json", "r") as file:
    fleet = json.load(file)


# ============================================================
# REGISTRATION AUTOCOMPLETE
# ============================================================

async def registration_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    current = current.strip().upper()
    matches = []

    for registration, data in fleet.items():

        aircraft = data["aircraft"]

        # Allows searching by either registration or aircraft.
        # Examples:
        #   CQ -> IF-CQRC
        #   A350 -> all A350 registrations
        if (
            current in registration.upper()
            or current in aircraft.upper()
        ):
            matches.append(
                app_commands.Choice(
                    name=f"{registration} — {aircraft}",
                    value=registration
                )
            )

    # Discord allows a maximum of 25 autocomplete results.
    return matches[:25]


# ============================================================
# CONFIRMATION BUTTONS
# ============================================================

class AssignmentConfirmation(discord.ui.View):

    def __init__(
        self,
        admin,
        pilot,
        username,
        aircraft,
        registration,
        origin,
        destination,
        trip_type
    ):
        super().__init__(timeout=120)

        self.admin = admin
        self.pilot = pilot
        self.username = username
        self.aircraft = aircraft
        self.registration = registration
        self.origin = origin
        self.destination = destination
        self.trip_type = trip_type


    # --------------------------------------------------------
    # CONFIRM BUTTON
    # --------------------------------------------------------

    @discord.ui.button(
        label="Confirm Assignment",
        style=discord.ButtonStyle.success,
        emoji="✈️"
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # Only the dispatcher who created the assignment
        # can confirm it.
        if interaction.user.id != self.admin.id:

            await interaction.response.send_message(
                "Only the dispatcher who created this assignment "
                "can confirm it.",
                ephemeral=True
            )

            return


        # Build flight list
        if self.trip_type == "round":

            flights = (
                f"**{self.origin} → {self.destination}**\n"
                f"**{self.destination} → {self.origin}**"
            )

            trip_name = "Round Trip"

        else:

            flights = (
                f"**{self.origin} → {self.destination}**"
            )

            trip_name = "One Way"


        # ----------------------------------------------------
        # FINAL PUBLIC EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title="✈️ Air France AIRCRAFT ASSIGNMENT",
            description=(
                f"Hi **{self.pilot.display_name}**,\n\n"

                f"You have been assigned the "
                f"**{self.aircraft}**, registration "
                f"**{self.registration}**, under the username "
                f"**{self.username}**, for the following "
                f"assigned flights:\n\n"

                f"{flights}\n\n"

                "Since this aircraft has been assigned "
                "specifically to you, please try to "
                "**complete the flight and land the aircraft "
                "whenever possible** so we can keep the "
                "schedule and fleet moving smoothly.\n\n"

                "If you're unable to complete or land the "
                "flight for any reason, please let one of "
                "the admins know so we can assist and find "
                "a solution without disrupting the schedule.\n\n"

                "Thank you for flying with "
                "**Air France Company**.\n\n"

                "**Enjoy your flight and safe travels, "
                "Captain!** ✈️"
            )
        )


        # Aircraft information
        embed.add_field(
            name="Aircraft",
            value=self.aircraft,
            inline=True
        )

        embed.add_field(
            name="Registration",
            value=self.registration,
            inline=True
        )

        embed.add_field(
            name="Trip",
            value=trip_name,
            inline=True
        )


        # Dispatcher information
        embed.set_footer(
            text=f"Assigned by {self.admin.display_name}"
        )


        # ----------------------------------------------------
        # REMOVE PRIVATE PREVIEW
        # ----------------------------------------------------

        await interaction.response.defer()

        await interaction.delete_original_response()


        # ----------------------------------------------------
        # PUBLISH ASSIGNMENT
        # ----------------------------------------------------

        await interaction.channel.send(
            content=self.pilot.mention,
            embed=embed
        )

        self.stop()


    # --------------------------------------------------------
    # CANCEL BUTTON
    # --------------------------------------------------------

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        emoji="✖️"
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.admin.id:

            await interaction.response.send_message(
                "Only the dispatcher who created this "
                "assignment can cancel it.",
                ephemeral=True
            )

            return


        await interaction.response.defer()

        await interaction.delete_original_response()

        self.stop()


# ============================================================
# BOT STARTUP
# ============================================================

@bot.event
async def on_ready():

    print(f"Version {VERSION} Build {BUILD}")
    print(f"✅ Logged in as {bot.user}")

    try:

        synced = await bot.tree.sync()

        print(
            f"✅ Synced {len(synced)} slash command(s)"
        )

    except Exception as e:

        print(
            f"❌ Error syncing commands: {e}"
        )


# ============================================================
# /assignaircraft COMMAND
# ============================================================

@bot.tree.command(
    name="assignaircraft",
    description="Assign an Air France aircraft to a pilot"
)

@app_commands.describe(

    pilot=(
        "The Discord user receiving the aircraft"
    ),

    infinite_flight_username=(
        "Pilot's Infinite Flight username"
    ),

    registration=(
        "Select an aircraft from the Air France fleet"
    ),

    origin=(
        "Departure airport ICAO code, e.g. LFPG"
    ),

    destination=(
        "Arrival airport ICAO code, e.g. KJFK"
    ),

    trip_type=(
        "Round Trip or One Way"
    )
)

@app_commands.choices(

    trip_type=[

        app_commands.Choice(
            name="Round Trip",
            value="round"
        ),

        app_commands.Choice(
            name="One Way",
            value="oneway"
        )
    ]
)

@app_commands.autocomplete(
    registration=registration_autocomplete
)

async def assignaircraft(

    interaction: discord.Interaction,

    pilot: discord.Member,

    infinite_flight_username: str,

    registration: str,

    origin: str,

    destination: str,

    trip_type: app_commands.Choice[str]

):

    # ========================================================
    # PERMISSION CHECK
    # ========================================================

    dispatcher_role = discord.utils.get(
        interaction.guild.roles,
        name="Aircraft Dispatcher"
    )

    is_dispatcher = (
        dispatcher_role is not None
        and dispatcher_role in interaction.user.roles
    )

    is_admin = (
        interaction.user.guild_permissions.administrator
    )

    if not is_dispatcher and not is_admin:

        await interaction.response.send_message(
            "❌ You don't have permission to assign aircraft.\n\n"
            "Only members with the **Aircraft Dispatcher** role "
            "or server administrators can use this command.",
            ephemeral=True
        )

        return


    # ========================================================
    # CLEAN INPUTS
    # ========================================================

    origin = origin.strip().upper()

    destination = destination.strip().upper()

    registration = registration.strip().upper()

    infinite_flight_username = (
        infinite_flight_username.strip()
    )


    # ========================================================
    # FLEET LOOKUP
    # ========================================================

    if registration not in fleet:

        await interaction.response.send_message(
            f"❌ **{registration}** is not registered in the "
            "Air France Company fleet.",
            ephemeral=True
        )

        return


    # Automatically determine the aircraft model.
    aircraft_model = fleet[registration]["aircraft"]


    # ========================================================
    # ICAO VALIDATION
    # ========================================================

    if not re.fullmatch(
        r"[A-Z]{4}",
        origin
    ):

        await interaction.response.send_message(

            f"❌ **{origin}** doesn't look like a valid "
            "ICAO code.\n\n"

            "Airport codes should contain four letters, "
            "such as **LFPG**.",

            ephemeral=True
        )

        return


    if not re.fullmatch(
        r"[A-Z]{4}",
        destination
    ):

        await interaction.response.send_message(

            f"❌ **{destination}** doesn't look like a valid "
            "ICAO code.\n\n"

            "Airport codes should contain four letters, "
            "such as **KJFK**.",

            ephemeral=True
        )

        return


    # ========================================================
    # BUILD ROUTE PREVIEW
    # ========================================================

    if trip_type.value == "round":

        route_preview = (

            f"**{origin} → {destination}**\n"

            f"**{destination} → {origin}**"
        )

    else:

        route_preview = (
            f"**{origin} → {destination}**"
        )


    # ========================================================
    # CREATE PRIVATE PREVIEW
    # ========================================================

    preview = discord.Embed(

        title="✈️ Aircraft Assignment Preview",

        description=(

            "Review this assignment before publishing it."
            "\n\n"

            f"**Pilot:** {pilot.mention}\n"

            f"**Infinite Flight Username:** "
            f"{infinite_flight_username}\n"

            f"**Aircraft:** {aircraft_model}\n"

            f"**Registration:** {registration}\n\n"

            "**Assigned Flight(s)**\n"

            f"{route_preview}"
        )
    )


    preview.set_footer(
        text=(
            "This preview is only visible to you. "
            "Confirm or cancel below."
        )
    )


    # ========================================================
    # CREATE BUTTONS
    # ========================================================

    view = AssignmentConfirmation(

        admin=interaction.user,

        pilot=pilot,

        username=infinite_flight_username,

        aircraft=aircraft_model,

        registration=registration,

        origin=origin,

        destination=destination,

        trip_type=trip_type.value
    )


    # ========================================================
    # SEND PRIVATE PREVIEW
    # ========================================================

    await interaction.response.send_message(

        embed=preview,

        view=view,

        ephemeral=True
    )


# ============================================================
# START BOT
# ============================================================

if not TOKEN:

    raise ValueError(
        "DISCORD_TOKEN was not found in your .env file."
    )


bot.run(TOKEN)