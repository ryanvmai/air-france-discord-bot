import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load the Discord token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")


@bot.tree.command(
    name="assignaircraft",
    description="Assign an Air France aircraft to a pilot"
)
@app_commands.describe(
    pilot="The Discord user receiving the aircraft",
    infinite_flight_username="Pilot's Infinite Flight username",
    aircraft_model="Aircraft model, e.g. A359",
    registration="Aircraft registration, e.g. F-HTYA",
    origin="Departure airport ICAO code, e.g. LFPG",
    destination="Arrival airport ICAO code, e.g. KJFK",
    trip_type="Round Trip or One Way"
)
@app_commands.choices(
    trip_type=[
        app_commands.Choice(name="Round Trip", value="round"),
        app_commands.Choice(name="One Way", value="oneway")
    ]
)
async def assignaircraft(
    interaction: discord.Interaction,
    pilot: discord.Member,
    infinite_flight_username: str,
    aircraft_model: str,
    registration: str,
    origin: str,
    destination: str,
    trip_type: app_commands.Choice[str]
):
    # Clean up formatting
    origin = origin.upper()
    destination = destination.upper()
    aircraft_model = aircraft_model.upper()
    registration = registration.upper()

    # Build route
    if trip_type.value == "round":
        flights = (
            f"**{origin} → {destination}**\n"
            f"**{destination} → {origin}**"
        )
    else:
        flights = f"**{origin} → {destination}**"

    message = f"""**Air France AIRCRAFT ASSIGNMENT**

Hi **{pilot.display_name}**,

You have been assigned the **{aircraft_model}**, registration **{registration}**, under the username **{infinite_flight_username}**, for the following assigned flights:

{flights}

Since this aircraft has been assigned specifically to you, please try to **complete the flight and land the aircraft whenever possible** so we can keep the schedule and fleet moving smoothly.

If you're unable to complete or land the flight for any reason, please let one of the admins know so we can assist and find a solution without disrupting the schedule.

Thank you for flying with **Air France Company**.

**Enjoy your flight and safe travels, Captain!** ✈️"""

    await interaction.response.send_message(message)


if not TOKEN:
    raise ValueError("DISCORD_TOKEN was not found in your .env file.")

bot.run(TOKEN)