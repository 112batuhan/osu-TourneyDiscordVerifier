import gspread
from oauth2client.service_account import ServiceAccountCredentials

class Sheet:

    def __init__(self,json_path):

        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
        self.gs = gspread.authorize(credentials)


    def set_current_sheet_data(self, sheet_id, worksheet_name, player_name_range, player_discord_range, verify_range):

        self.current_work_sheet = self.gs.open_by_key(sheet_id).worksheet(worksheet_name)

        self.player_names = self.current_work_sheet.range(player_name_range)
        self.discord_names = self.current_work_sheet.range(player_discord_range)
        self.verify = self.current_work_sheet.range(verify_range)


    def update_player(self, player_name, discord_tag):

        for player_cell, discord_cell, verify_cell in zip(self.player_names, self.discord_names, self.verify):

            if player_cell.value == player_name and discord_cell.value == discord_tag:

                verify_cell.value = "TRUE"
                self.current_work_sheet.update_cells([verify_cell], value_input_option='USER_ENTERED')
                return

        raise KeyError("Searched player could not find.")

    def get_player_list(self):

        player_list = []
        for player_cell, discord_cell, verify_cell in zip(self.player_names, self.discord_names, self.verify):

            if verify_cell.value == "TRUE":

                player_list.append([player_cell.value, discord_cell.value])

        return player_list

