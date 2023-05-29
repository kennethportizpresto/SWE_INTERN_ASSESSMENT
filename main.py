# Kenneth Portiz Presto
import pandas as pd
from collections import defaultdict
''' 
Chokepoint is not a rectangle using the formula d = sqrt((x2-x1)^2 + (y2 - y1)^2)... d1 != d2 ergo
chokepoint is a polygon. 
'''

class ProcessGameState:
    def __init__(self, dataFile):
        """
        Filters valid rows from datafile. 
        Creates a dictionary of each player in a team. 
        Lists chokepoint edges. 
        """
        self.dataFile = dataFile
        valid_ZBounds = (dataFile['z'] <= 421) & (dataFile['z'] >= 285)
        self.playerData = dataFile[valid_ZBounds]

        self.allPlayers = defaultdict(set)
        self.listAllPlayers = set(zip(self.playerData['team'], self.playerData['side'], self.playerData['player']))
        for t,s,p in self.listAllPlayers:
            self.allPlayers[(t,s)].add(p)
        
        self.polygonEdges = [((-2472, 1233), (-1565,580)), ((-1565,580), 
                        (-1735,250)), ((-1735,250), (-2024, 398)), 
                        ((-2024, 398), (-2806,742)), ((-2806,742), (-2472, 1233))]
    
    def chokepointDominance(self):
        """ 
        Creates a defaultdict with team and side as a tuple as the key and 
        the value as the number of points inside chokepoint.
        Returns the key with the maximum amt of points inside the chokepoint.
        """
        valid_Points = set(zip(self.playerData['x'], self.playerData['y'], self.playerData['team'], self.playerData['side']))
        chokepointData = defaultdict(int)

        for x,y,t,s in valid_Points:
            if self._inside_chokepoint(x,y)== True:
                chokepointData[(t,s)] += 1
        return max(chokepointData.items(), key=lambda x:x[1])[0]

    def _inside_chokepoint(self, x, y, flag=False):
        """ 
        Used https://en.wikipedia.org/wiki/Even%E2%80%93odd_rule as a framework.
        HelperFunc uses Ray Casting Algorithm to check if point is inside polygon. 
        Returns a boolean.
        """ 
        for edge in self.polygonEdges:
            (x1, y1), (x2,y2) = edge
            if (y1 > y) != (y2 > y): # Ray Cast Condition 1
                slope = (x-x1)*(y2-y1)-(x2-x1)*(y-y1) # Formula
                if (y1 > y2) != (slope < 0): # Ray Cast Condition 2
                    flag = not flag
        return flag

    def averageTime(self, team, side, area):
        """
        Function returns the average time that Team2 on side T enters the BombsiteB 
        with more than one player with a total of at least 2 weapons that are either 
        Rifles or SMGs (i.e. 1 rifle and 1 smg or 2 rifle and 0 smg or 0 rifle and 2 smg)
        """
        times = self._list_player_times(team, side, area)
        sum = 0

        for k,v in times.items():
            sum += k[0]
        return sum// len([k for k,v in times.items() if len(v) >= 1])
    
    def _list_player_times(self, team, side, area):
        """
        HelperFunc filters player's enter/exited times based on team, side, place, and weapon.
        Returns a dictionary. Dictionary keys are tuples and values are a list of tuples.
        """
        keys = []
        teamMemmber = self.allPlayers[(team, side)]

        for t in teamMemmber:
            data = self.dataFile[(self.dataFile['area_name'] == area) & (self.dataFile['player'] == t) & (self.dataFile['team'] == team) & (self.dataFile['side'] == "T") & (self.dataFile['is_alive'] == True)]
            weaponClass = self._list_times(data)
            keys.extend(weaponClass)

        # Creates a dictionary with all enter/exit as keys and values as empty lists
        times = {k:list() for k in keys}

        # For each key check if a time's enter time is less than the key's exit time. 
        # If true, append enter/exit time because of overlap.
        for k in keys:
            for tmp in keys:
                if k != tmp and k[0] < tmp[1]:
                    times[tmp].append(k)
        return times

    def _list_times(self, dataFrame):
        """
        HelperFunc filters times when a player had entered/exited the bombsite. 
        Returns a list of tuples.
        """
        time = self._list_valid_times(dataFrame)
        result = []
        entered_exited = []

        if len(time) != 1:
            for i in range(len(time)-1):
                entered_exited.append(time[i])
                if time[i+1] - time[i] != 1:
                    result.append((entered_exited[0], entered_exited[-1]))
                    entered_exited = []
                if i+1 == len(time)-1:
                    entered_exited.append(time[i+1])
                    result.append((entered_exited[0], entered_exited[-1]))
        else:
            result.append((time[0], time[0]))
        return result
    
    def _list_valid_times(self, dataFrame):
        """
        HelperFunc filters times when a player enters BombsiteB with a Rifle or SMG. 
        Returns a list of integers.
        """
        time = []

        for k,v in zip(dataFrame['seconds'], dataFrame['inventory']):
            if v[0]['weapon_class'] == 'Rifle' or v[0]['weapon_class'] == 'SMG':
                if k not in time:
                    time.append(k)
        if 0 in time:
            add = time[time.index(0) - 1] + 1
            for i in range(time.index(0), len(time)):
                time[i] += add
        return time
    
    def heatMap(self, team, side, area):
        """
        Function filters desired coordinates and averages x, y, and z coordinate points. 
        Returns a 3 element tuple.
        """
        locations = []
        teamMemmber = self.allPlayers[(team, side)]

        for t in teamMemmber:
            data = self.dataFile[(self.dataFile['area_name'] == area) & (self.dataFile['player'] == t) & (self.dataFile['team'] == team) & (self.dataFile['side'] == "CT") & (self.dataFile['is_alive'] == True)]      
            for x,y,z in set(zip(data['x'], data['y'], data['z'])):
                locations.append([x,y,z])
        x_average = sum([x for x,y,z in locations])//len([x for x,y,z in locations]) 
        y_average = sum([y for x,y,z in locations])//len([y for x,y,z in locations]) 
        z_average = sum([z for x,y,z in locations])//len([z for x,y,z in locations]) 
        return (x_average, y_average, z_average)

if __name__ == "__main__":
    df = pd.read_pickle("game_state_frame_data.pickle")
    CounterStrikeMatch = ProcessGameState(df)
    dominantTeamSide = CounterStrikeMatch.chokepointDominance()
    print("Is entering via the light blue boundary a common strategy used by Team2 on T (terrorist) side?:")
    print("{}, {} on {} side uses the chokepoint as a common strategy.\n".format(dominantTeamSide == ('Team2', 'T'), dominantTeamSide[0], dominantTeamSide[1]))
    print("What is the average timer that Team2 on T (terrorist) side enters 'BombsiteB' with least 2 rifles or SMGs?:\n{} seconds\n".format(CounterStrikeMatch.averageTime('Team2', 'T', 'BombsiteB')))
    print("Now that we\'ve gathered data on Team2 T side, let's examine their CT (counter-terrorist) Side. Using the same data set, tell our coaching staff where you suspect them to be waiting inside 'BombsiteB':\nThe Coordinate: {} is around where they will be waiting.".format(CounterStrikeMatch.heatMap('Team2', 'CT', 'BombsiteB')))
