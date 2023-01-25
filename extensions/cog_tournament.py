#### #### Imports #### ####

import discord
from discord.ext import commands
from discord import app_commands
from main import MC_Bot_Client


#### #### Static Properties #### ####

#### #### Class #### ####


class Cog_Tournament(commands.Cog):  # Admin/authenticated roles only.

    #### #### Properties #### ####

    bot_client: MC_Bot_Client

    #### #### Structors #### ####

    def __init__(self, bot_client: MC_Bot_Client) -> None:
        self.bot_client = bot_client  # create reference to the bot

    #### #### Slash Commands #### ####

    @app_commands.command(name='create_tournament', description='Create a brand new tournament!')
    async def create_tournament(
            self,
            interaction: discord.Interaction,
            tournament_name: str,
            tournament_description: str
    ) -> None:
        await interaction.response.defer(thinking=True)  # This could take longer than 3 s.

        tournament_json = await self.bot_client.api_request( # Returns the created tournament
            method='POST',
            uri='tournaments.json',
            params={
                'tournament[name]': tournament_name,
                'tournament[description]': tournament_description
            }
        )

        await interaction.followup.send(
            content='Tournament created!',
            embed=create_tournament_embed(tournament_json)
        )
        return

    @app_commands.command(name='list_tournaments', description='List all tournaments available.')
    async def list_tournaments(
            self,
            interaction: discord.Interaction
    ) -> None:
        await interaction.response.defer(thinking=False)  # this could take longer than 3 s

        tournament_list = await self.bot_client.api_request(
            method='GET',
            uri='tournaments.json'
        )
        if len(tournament_list) == 0: await interaction.followup.send('No tournaments to list!')

        tournament_list_as_an_embed = discord.Embed(title='Tournament List')
        for tournament_json in tournament_list:
            tournament_list_as_an_embed.add_field(
                name=tournament_json['tournament']['name'],
                value=tournament_json['tournament']['id']
            )

        await interaction.followup.send(
            embed=tournament_list_as_an_embed,
            view=View_TournamentList(tournament_list)
        )


#### #### Views #### ####


class View_TournamentList(discord.ui.View):
    def __init__(self, tournament_list: dict, timeout=180) -> None:
        super().__init__(timeout=timeout) #1. Create the view which will contain the dropdown
        self.add_item(self.Select_TournamentList(tournament_list)) #2. ->
        return

    class Select_TournamentList(discord.ui.Select):
        def __init__(self, tournament_list: dict) -> None:
            tournament_list = [discord.SelectOption( #2. Then, add all the tournaments to the list as selectoptions
                label=tournament['tournament']['name'],
                value=tournament['tournament']['id']
            ) for tournament in tournament_list]

            super().__init__( #3. Create the dropdown using the created list of tournament selectoptions
                placeholder="Select a tournament!",
                options=tournament_list[:24] # Selectoptions have a max of 25 elements! # TODO add paginator
            )
            return

        async def callback(self, interaction: discord.Interaction): #4. When a tournament is selected, display it
            await interaction.response.defer(thinking=False)  # Interactions time out after 3s, so defer it

            bot_client = interaction.client # type: MC_Bot_Client
            selected_tournament_data = await bot_client.api_request(
                method='GET',
                uri=f'tournaments//{self.values[0]}.json'
            ) #5. Get the tournament data from the ID, since i dont want to pass the tourney info thru the value attr.

            await interaction.followup.send(
                embed=create_tournament_embed(selected_tournament_data),
                view=self.View_ManageTournament(selected_tournament_data)
            ) #6. Send embed to display the tourney, and show the options for it (start, update, cancel)
            return

        class View_ManageTournament(discord.ui.View):
            def __init__(self, tournament_data: dict) -> None:
                super().__init__() #7. Create the view with the buttons, and then add the buttons!
                self.add_item(self.Button_TournamentStart(tournament_data))
                self.add_item(self.Button_TournamentUpdate(tournament_data))
                self.add_item(self.Button_TournamentCancel(tournament_data))
                return

            class Button_TournamentStart(discord.ui.Button): # TODO
                def __init__(self, tournament_data: dict) -> None:
                    self.tournament_data = tournament_data
                    super().__init__(label='Start')
                    return

                async def callback(self, interaction: discord.Interaction) -> None:
                    await interaction.response.send_message('Feature not yet implemented.')
                    return

            class Button_TournamentUpdate(discord.ui.Button):
                def __init__(self, tournament_data: dict) -> None:
                    self.tournament_data = tournament_data
                    super().__init__(label='Update')
                    return

                async def callback(self, interaction: discord.Interaction) -> None:
                    await interaction.response.send_modal(self.Modal_TournamentUpdate(self.tournament_data))
                    return

                class Modal_TournamentUpdate(discord.ui.Modal):
                    def __init__(self, tournament_data: dict) -> None:
                        self.tournament_data = tournament_data
                        super().__init__(title='Update Tournament', timeout=300)

                        tournament_options = ['name', 'description']
                        for tournament_option in tournament_options:
                            self.add_item(
                                discord.ui.TextInput(
                                    label=tournament_option,
                                    default=self.tournament_data['tournament'][tournament_option]
                                )
                            )
                        return

                    async def on_submit(self, interaction: discord.Interaction):
                        await interaction.response.defer(thinking=True) #Only get 3s to respond, make sure no timeout

                        tournament_option_text_input: discord.ui.TextInput  # typehint so ide won't complain
                        tournament_parameters_to_update = {}
                        for tournament_option_text_input in self.children:
                            parameter_key = f'tournament[{tournament_option_text_input.label}]'
                            parameter_value = tournament_option_text_input.value
                            tournament_parameters_to_update[parameter_key] = parameter_value

                        bot_client = interaction.client # type: MC_Bot_Client
                        await bot_client.api_request(
                            'PUT',
                            f'tournaments/{self.tournament_data["tournament"]["id"]}.json',
                            tournament_parameters_to_update
                        )

                        await interaction.followup.send(
                            f'Tournament <**{self.tournament_data["tournament"]["name"]}**> updated!'
                        )
                        return

            class Button_TournamentCancel(discord.ui.Button):
                def __init__(self, tournament_data: dict) -> None:
                    self.tournament_data = tournament_data
                    super().__init__(label='Cancel')
                    return

                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.defer(thinking=True)  # This could take longer than 3 s.

                    await interaction.followup.send(
                        content='Delete the following tournament?',
                        embed=create_tournament_embed(self.tournament_data),
                        view=self.View_ConfirmTournamentCancel(self.tournament_data)
                    )
                    return

                class View_ConfirmTournamentCancel(discord.ui.View):
                    def __init__(self, tournament_data: dict) -> None:
                        super().__init__()
                        self.add_item(self.Button_ConfirmTournamentCancel(tournament_data))
                        return

                    class Button_ConfirmTournamentCancel(discord.ui.Button):
                        def __init__(self, tournament_data: dict) -> None:
                            self.tournament_data = tournament_data
                            super().__init__(label='Confirm', style=discord.ButtonStyle.danger)
                            return

                        async def callback(self, interaction: discord.Interaction) -> None:
                            await interaction.response.defer(thinking=True)  # Only get 3s to respond, don't timeout

                            bot_client = interaction.client # type: MC_Bot_Client
                            await bot_client.api_request(
                                method="DELETE",
                                uri=f'tournaments//{self.tournament_data["tournament"]["id"]}.json'
                            )

                            await interaction.followup.send(
                                f'<**{self.tournament_data["tournament"]["name"]}**> has been cancelled.'
                            )
                            return


#### #### Utility #### ####


def create_tournament_embed(tournament_json):
    tournament_json = tournament_json['tournament']
    tournament_embed = discord.Embed(
        title=tournament_json['name'],
        description=tournament_json['description'],
        url=tournament_json['full_challonge_url'],
    )
    tournament_embed.thumbnail.url = tournament_json['live_image_url']
    return tournament_embed

#### #### #### ####


async def setup(bot_client: MC_Bot_Client) -> None:
    await bot_client.add_cog(Cog_Tournament(bot_client))

#### #### End of File #### ####
