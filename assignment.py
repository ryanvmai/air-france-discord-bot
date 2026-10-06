import discord
from discord import app_commands
from discord.ext import commands

TOKEN = "c187f1130105ba3bd2dbb73e08c03e46bab5706b3d2260b06a7db313bb4b8ba0"

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.tree.command(
    name="assignaircraft",
    description="Assign an Air France aircraft to a pilot"
)
@app_commands.describe(
    pilot="Pilot receiving the aircraft",
    infinite_flight_username="Pilot's Infinite Flight username",
    aircraft_model="Aircraft type, e.g. A359",
    registration="Aircraft registration",
    origin="Departure airport ICAO code",
    destination="Arrival airport ICAO code",
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

    origin = origin.upper()
    destination = destination.upper()
    aircraft_model = aircraft_model.upper()
    registration = registration.upper()

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


bot.run(TOKEN)