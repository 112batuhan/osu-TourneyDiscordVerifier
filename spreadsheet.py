import gspread
from oauth2client.service_account import ServiceAccountCredentials

class Sheet:

    def __init__(self,json_path):

        self.json_path = json_path
        
    def authhorise(self):
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.json_path, scope)
        self.gs = gspread.authorize(credentials)


    def update_player(self, player_name, discord_tag, sheet_id, worksheet_name, player_range, discord_name_range, verify_range):

        self.authhorise()
        current_work_sheet = self.gs.open_by_key(sheet_id).worksheet(worksheet_name)

        player_names = current_work_sheet.range(player_range)
        discord_names = current_work_sheet.range(discord_name_range)
        verify = current_work_sheet.range(verify_range)

        for player_cell, discord_cell, verify_cell in zip(player_names, discord_names, verify):

            if player_cell.value == player_name and discord_cell.value == discord_tag:

                verify_cell.value = "TRUE"
                current_work_sheet.update_cells([verify_cell], value_input_option='USER_ENTERED')
                return

        raise KeyError("Searched player could not find.")

    def get_player_list(self, sheet_id, worksheet_name, player_range, discord_name_range, verify_range):

        self.authhorise()
        current_work_sheet = self.gs.open_by_key(sheet_id).worksheet(worksheet_name)

        player_names = current_work_sheet.range(player_range)
        discord_names = current_work_sheet.range(discord_name_range)
        verify = current_work_sheet.range(verify_range)

        player_list = []
        for player_cell, discord_cell, verify_cell in zip(player_names, discord_names, verify):

            if verify_cell.value == "TRUE":

                player_list.append([player_cell.value, discord_cell.value])

        return player_list

    #a bit too hardcoded but whatever
    def set_qualifier_settings(self, sheet_id, worksheet_name, player_range, room_name_range, referee_range, day_range, time_range, match_link_range):

        self.authhorise()

        self.player_range = player_range
        self.room_name_range = room_name_range
        self.referee_range = referee_range
        self.day_range = day_range
        self.time_range = time_range
        self.match_link_range = match_link_range

        self.current_work_sheet = self.gs.open_by_key(sheet_id).worksheet(worksheet_name)

    def create_room(self, room_id, day_setting, time_setting):

        self.authhorise()

        room_names = self.current_work_sheet.range(self.room_name_range)
        days = self.current_work_sheet.range(self.day_range)
        times =  self.current_work_sheet.range(self.time_range)

        for room, day, time in zip(room_names, days, times):

            if room.value == "":

                room.value = room_id
                day.value = day_setting
                time.value = time_setting

                self.current_work_sheet.update_cells([room, day, time], value_input_option='USER_ENTERED')
                break

    def delete_room(self, room_id):

        self.authhorise()

        room_names = self.current_work_sheet.range(self.room_name_range)
        days = self.current_work_sheet.range(self.day_range)
        times =  self.current_work_sheet.range(self.time_range)
        referees = self.current_work_sheet.range(self.referee_range)
        match_links =  self.current_work_sheet.range(self.match_link_range)
        players = self.current_work_sheet.range(self.player_range)

        for index, (room, day, time, referee, match_link) in enumerate(zip(room_names,days,times,referees,match_links)):
            
            if room.value == room_id:
                
                room.value = ""
                day.value = ""
                time.value = ""
                referee.value = ""
                match_link.value = ""
                cells_to_update = [room,day,time,referee,match_link]

                for player in players[index*16:(index+1)*16]:
                    player.value = ""
                    cells_to_update.append(player)

                self.current_work_sheet.update_cells(cells_to_update, value_input_option='USER_ENTERED')
                break
    
    def add_referee(self, room_id, referee_setting):

        self.authhorise()

        room_names = self.current_work_sheet.range(self.room_name_range)
        referees = self.current_work_sheet.range(self.referee_range)

        for room, referee in zip(room_names, referees):

            if room.value == room_id:

                referee.value = referee_setting
                self.current_work_sheet.update_cells([referee], value_input_option='USER_ENTERED')
                break

    def remove_referee(self, room_id):

        self.authhorise()

        room_names = self.current_work_sheet.range(self.room_name_range)
        referees = self.current_work_sheet.range(self.referee_range)

        for room, referee in zip(room_names, referees):

            if room.value == room_id:

                referee.value = ""
                self.current_work_sheet.update_cells([referee], value_input_option='USER_ENTERED')
                break

    def add_mp_link(self, room_id, mp_link_setting):

        self.authhorise()

        room_names = self.current_work_sheet.range(self.room_name_range)
        mp_links =  self.current_work_sheet.range(self.match_link_range)

        for room, mp_link in zip(room_names, mp_links):

            if room.value == room_id:

                mp_link.value = mp_link_setting
                self.current_work_sheet.update_cells([mp_link], value_input_option='USER_ENTERED')
                break

    def update_players(self, room_id, player_list):

        self.authhorise()

        player_list = player_list + (16-len(player_list))*[""]

        room_names = self.current_work_sheet.range(self.room_name_range)
        players = self.current_work_sheet.range(self.player_range)

        for index, room in enumerate(room_names):
            
            if room.value == room_id:
                
                cells_to_update = []
                for player_name, player_cell in zip(player_list, players[index*16:(index+1)*16]):
                    player_cell.value = player_name
                    cells_to_update.append(player_cell)
                    self.current_work_sheet.update_cells(cells_to_update, value_input_option='USER_ENTERED')
                break
