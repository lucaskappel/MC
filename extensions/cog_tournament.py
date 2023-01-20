#### #### Imports #### ####

import aiohttp, json
import discord
from discord.ext import commands
from discord import app_commands


#### #### Static Properties #### ####

#### #### Class #### ####


class Cog_Tournament(commands.Cog):  # Admin/authenticated roles only.

    #### #### Properties #### ####

    bot_client = None
    api_client = None
    bot_config = {}

    #### #### Structors #### ####

    def __init__(self, bot_client: commands.Bot) -> None:
        self.bot_client = bot_client  # create a reference to the bot
        with open(r"config.json", encoding='utf8') as config_file:
            self.bot_config = json.load(config_file)
        return

    async def cog_load(self) -> None:

        # Create the aiohttp session and authenticate it. We will use the same client until the bot shuts down.
        self.api_client = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(
                self.bot_config['CHALLONGE_USERNAME'],
                self.bot_config['CHALLONGE_TOKEN']
            ))
        return

    async def cog_unload(self) -> None:
        await self.api_client.close()
        return

    #### #### Slash Commands #### ####

    @app_commands.command(
        name='list_tournaments',
        description='List all tournaments available.'
    )
    async def list_tournaments(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)  # this could take longer than 3 s

        tournament_list = await api_request(self.api_client, 'GET', 'tournaments.json')
        if len(tournament_list) == 0:
            await interaction.followup.send('No tournaments to list!')

        tournament_list_as_an_embed = discord.Embed(title='Tournament List')
        for tournament_json in tournament_list:
            tournament_list_as_an_embed.add_field(
                name=tournament_json['tournament']['name'],
                value=tournament_json['tournament']['id']
            )

        await interaction.followup.send(
            embed=tournament_list_as_an_embed,
            view=selectview_tournament_list(
                self.api_client, await api_request(self.api_client, method='GET', uri='tournaments.json')
            )
        )
        return

    @app_commands.command(name='tournament_create')
    async def tournament_create(
            self,
            interaction: discord.Interaction,
            tournament_name: str,
            tournament_description: str
    ) -> None:
        await interaction.response.defer(thinking=True)  # This could take longer than 3 s.

        tournament_information = {
                'tournament[name]': tournament_name,
                'tournament[description]': tournament_description
            }

        tournament_json = await api_request(
            self.api_client,
            'POST',
            'tournaments.json',
            tournament_information
        )

        await interaction.followup.send(
            content='Tournament created!',
            embed=create_tournament_embed(tournament_json)
        )
        return


#### #### Views #### ####


class selectview_tournament_list(discord.ui.View):
    # This class is the base building block required to create a UI element
    def __init__(self, api_client, tournament_list, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(self.select_tournament_list(api_client, tournament_list))

    class select_tournament_list(discord.ui.Select):  # View class to display the card in a Q&A
        def __init__(self, api_client, tournament_list):
            # TODO add button to page through tournaments if necessary
            self.api_client = api_client
            tournament_list = [discord.SelectOption(
                label=tournament['tournament']['name'],
                value=tournament['tournament']['id']
            ) for tournament in tournament_list]

            super().__init__(
                placeholder="Select a tournament!",
                options=tournament_list[:24]  # Make sure you don't put more options than is allowed! First 24 only.
            )

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(thinking=False)  # This could take longer than 3s.
            selected_tournament_info = await api_request(
                self.api_client,
                'GET',
                f'tournaments//{self.values[0]}.json'
            )
            await interaction.followup.send(
                embed=create_tournament_embed(selected_tournament_info),
                view=buttonview_tournament_manage(self.api_client, self.values[0])
            )
            # Delete, start, open registration, update info
            return


class buttonview_tournament_manage(discord.ui.View):
    def __init__(self, api_client: aiohttp.ClientSession, tournament_id: str, *, timeout=180):
        self.api_client = api_client
        self.tournament_id = tournament_id
        super().__init__(timeout=timeout)
        self.add_item(self.button_to_start_tournament(api_client, tournament_id))
        self.add_item(self.button_to_update_tournament(api_client, tournament_id))
        self.add_item(self.button_to_cancel_tournament(api_client, tournament_id))

    class button_to_start_tournament(discord.ui.Button):
        def __init__(self, api_client: aiohttp.ClientSession, tournament_id: str):
            self.tournament_id = tournament_id
            self.api_client = api_client
            super().__init__()
            self.label = 'Start Tournament'

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)  # This could take longer than 3 s.
            await interaction.followup.send(f'Starting tournament <{self.tournament_id}>.')

    class button_to_update_tournament(discord.ui.Button):
        def __init__(self, api_client: aiohttp.ClientSession, tournament_id: str):
            self.tournament_id = tournament_id
            self.api_client = api_client
            super().__init__()
            self.label = 'Update Tournament'

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)  # This could take longer than 3 s.
            await interaction.followup.send(f'Updating tournament <{self.tournament_id}>.')

    class button_to_cancel_tournament(discord.ui.Button):
        def __init__(self, api_client: aiohttp.ClientSession, tournament_id: str):
            self.tournament_id = tournament_id
            self.api_client = api_client
            super().__init__()
            self.label = 'Cancel Tournament'

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)  # This could take longer than 3 s.
            await interaction.followup.send(
                content='Delete the following tournament?',
                embed=create_tournament_embed(
                    await api_request(self.api_client, "GET", f'tournaments//{self.tournament_id}.json')),
                view=self.buttonview_confirm_tournament_deletion(self.api_client, self.tournament_id)
            )
            return

        class buttonview_confirm_tournament_deletion(discord.ui.View):
            def __init__(self, api_client: aiohttp.ClientSession, tournament_id: str, timeout=180) -> None:
                super().__init__(timeout=timeout)
                self.add_item(self.button_confirm_tournament_deletion(api_client, tournament_id))

            class button_confirm_tournament_deletion(discord.ui.Button):
                def __init__(self, api_client: aiohttp.ClientSession, tournament_id: str) -> None:
                    self.tournament_id = tournament_id
                    self.api_client = api_client
                    super().__init__()
                    self.label = 'Confirm Tournament Cancel'
                    return

                async def callback(self, interaction: discord.Interaction) -> None:
                    await interaction.response.defer(thinking=True)  # This could take longer than 3 s.
                    await api_request(self.api_client, "DELETE", f'tournaments//{self.tournament_id}.json')
                    await interaction.followup.send(f'Tournament with ID <{self.tournament_id}> has been cancelled.')
                    return


#### #### Utility #### ####


async def api_request(api_client: aiohttp.ClientSession, method: str, uri: str, params=None) -> dict:
    if params is None: params = {}

    api_url = r'https://api.challonge.com/v1/' + uri

    if method == "GET":
        request_response = await api_client.get(api_url, params=params)
    elif method == "POST":
        request_response = await api_client.post(api_url, params=params)
    elif method == "DELETE":
        request_response = await api_client.delete(api_url, params=params)
    else:
        raise Exception('Invalid method. GET, POST, or DELETE are allowed.')

    if request_response.status != 200:
        print(f'Error: API call returned status <{request_response.status}>')

    return_request_response = await request_response.json()
    request_response.close()

    return return_request_response


def create_tournament_embed(tournament_json):
    tournament_json = tournament_json['tournament']
    tournament_embed = discord.Embed(
        title=tournament_json['name'],
        description=tournament_json['description'],
        url=tournament_json['full_challonge_url'],
    )
    tournament_embed.thumbnail.url = tournament_json['live_image_url']

    tournament_embed.add_field(
        name=f'{tournament_json["game_name"]} Tournament',
        value=tournament_json['state']
    )

    return tournament_embed

#### #### #### ####


async def setup(bot_client: commands.Bot) -> None:
    await bot_client.add_cog(Cog_Tournament(bot_client))

#### #### End of File #### ####
