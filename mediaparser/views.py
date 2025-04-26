import os
import ffmpeg
import discord.ui
import asyncio
import discord
from redbot.core import commands


class ResolutionView(discord.ui.View):
    def __init__(
        self,
        message: discord.Message,
        path: str,
        media_parser,
        embed_menu: discord.Message,
    ):
        super().__init__()
        self.message = message
        self.path = path
        self.media_parser = media_parser
        self.embed_menu = embed_menu
        self.selected_file = None
        self.clear_items()
        self.add_item(FileSelect(path))
        self.ffmpeg_processing = None

    async def scale_videos(self, resolution: str):
        resolution_map = {"1080p": "1920", "720p": "1280", "480p": "854", "360p": "640"}
        target_width = resolution_map.get(resolution)

        ctx: commands.Context = await self.media_parser.bot.get_context(self.message)

        if self.selected_file:
            input_path = os.path.join(self.path, self.selected_file)
            output_path = os.path.join(
                self.path, f"{os.path.splitext(self.selected_file)[0]}_{resolution}.mp4"
            )

            try:
                async with ctx.typing():
                    probe = ffmpeg.probe(input_path)
                    streams = probe.get("streams", [])
                    if streams:
                        video_stream = next(
                            (s for s in streams if s["codec_type"] == "video"), None
                        )
                        if video_stream:
                            height = video_stream.get("height")
                            width = video_stream.get("width")
                            if height and width:
                                new_height = int(height * (int(target_width) / width))
                                if new_height % 2 != 0:
                                    new_height -= 1

                                await asyncio.to_thread(
                                    ffmpeg.input(input_path)
                                    .output(
                                        output_path,
                                        vf=f"scale={target_width}:{new_height}",
                                        loglevel="quiet",
                                    )
                                    .run,
                                    overwrite_output=False,
                                )

                                self.ffmpeg_processing = None
                            else:
                                print(
                                    f"Error: Height or width not found in video stream for {self.selected_file}"
                                )
                        else:
                            print(
                                f"Error: No video stream found in {self.selected_file}"
                            )
                    else:
                        print(f"Error: No streams found in {self.selected_file}")
            except ffmpeg.Error as e:
                print(e.stderr)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            finally:
                try:
                    os.remove(input_path)
                    os.rename(output_path, input_path)
                except OSError:
                    pass

    async def disable_buttons(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, discord.ui.Button) or isinstance(
                child, discord.ui.Select
            ):
                child.disabled = True
        await interaction.edit_original_response(view=self)

    async def show_resolution_buttons(self):
        """Dynamically add resolution buttons after file selection."""
        self.clear_items()  # Remove the FileSelect dropdown
        self.add_item(self.button_1080p)
        self.add_item(self.button_720p)
        self.add_item(self.button_480p)
        self.add_item(self.button_360p)
        self.add_item(self.button_cancel)
        await self.embed_menu.edit(view=self)  # Edit the embed_menu message directly

    @discord.ui.button(label="1080p", style=discord.ButtonStyle.primary, emoji="🎥")
    async def button_1080p(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.message.author.id:
            return await interaction.response.send_message(
                "You are not allowed to use this button.", ephemeral=True
            )
        self.ffmpeg_processing = True

        await interaction.response.defer(ephemeral=True)
        await self.disable_buttons(interaction)
        await self.embed_menu.delete()
        await self.scale_videos("1080p")
        time_elapsed = 0
        while self.ffmpeg_processing and time_elapsed <= 120:
            await asyncio.sleep(10)
            time_elapsed += 10

        if time_elapsed >= 120:
            return

        else:
            await self.media_parser.send_video(
                self.message, True, self.path, self.selected_file
            )

    @discord.ui.button(label="720p", style=discord.ButtonStyle.primary, emoji="📺")
    async def button_720p(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.message.author.id:
            return await interaction.response.send_message(
                "You are not allowed to use this button.", ephemeral=True
            )
        self.ffmpeg_processing = True

        await interaction.response.defer(ephemeral=True)
        await self.disable_buttons(interaction)
        await self.embed_menu.delete()
        await self.scale_videos("720p")
        time_elapsed = 0
        while self.ffmpeg_processing and time_elapsed <= 120:
            await asyncio.sleep(10)
            time_elapsed += 10

        if time_elapsed >= 120:
            return

        else:
            await self.media_parser.send_video(
                self.message, True, self.path, self.selected_file
            )

    @discord.ui.button(label="480p", style=discord.ButtonStyle.primary, emoji="📹")
    async def button_480p(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.message.author.id:
            return await interaction.response.send_message(
                "You are not allowed to use this button.", ephemeral=True
            )
        self.ffmpeg_processing = True

        await interaction.response.defer(ephemeral=True)
        await self.disable_buttons(interaction)
        await self.embed_menu.delete()
        await self.scale_videos("480p")
        time_elapsed = 0
        while self.ffmpeg_processing and time_elapsed <= 120:
            await asyncio.sleep(10)
            time_elapsed += 10

        if time_elapsed >= 120:
            return

        else:
            await self.media_parser.send_video(
                self.message, True, self.path, self.selected_file
            )

    @discord.ui.button(label="360p", style=discord.ButtonStyle.primary, emoji="📱")
    async def button_360p(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.message.author.id:
            return await interaction.response.send_message(
                "You are not allowed to use this button.", ephemeral=True
            )
        self.ffmpeg_processing = True

        await interaction.response.defer(ephemeral=True)
        await self.disable_buttons(interaction)
        await self.embed_menu.delete()
        await self.scale_videos("360p")
        time_elapsed = 0
        while self.ffmpeg_processing and time_elapsed <= 120:
            await asyncio.sleep(10)
            time_elapsed += 10

        if time_elapsed >= 120:
            return

        else:
            await self.media_parser.send_video(
                self.message, True, self.path, self.selected_file
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="✖️")
    async def button_cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.message.author.id:
            return await interaction.response.send_message(
                "You are not allowed to use this button.", ephemeral=True
            )
        await self.disable_buttons(interaction)
        await self.embed_menu.delete()
        await self.media_parser.send_video(
            self.message, False, self.path, self.selected_file
        )  # Sends a False to the send_video function which means that the video isnt sent.
        await interaction.response.send_message("Download cancelled", ephemeral=True)


class FileSelect(discord.ui.Select):
    def __init__(self, path: str):
        self.path = path
        files = [
            file
            for file in os.listdir(path)
            if file.endswith((".mp4", ".mkv", ".avi", ".jpg", ".jpeg", ".png", ".gif"))
        ]
        self.file_dict = {
            f"Post {i+1}{os.path.splitext(file)[1]}": file
            for i, file in enumerate(files)
        }  # I regret making this one line

        options = [
            discord.SelectOption(label=key, value=self.file_dict[key])
            for key in self.file_dict.keys()
        ]
        super().__init__(
            placeholder="Choose a file...", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view: ResolutionView = self.view
        if interaction.user.id != view.message.author.id:
            return await interaction.response.send_message(
                "You are not allowed to use this select.", ephemeral=True
            )

        view.selected_file = self.values[0]
        inv_map = {v: k for k, v in self.file_dict.items()}  # This is stupid
        await interaction.response.send_message(
            f"Selected file: {inv_map[self.values[0]]}",
            ephemeral=True,
        )

        await view.show_resolution_buttons()  # Update the embed_menu with buttons
