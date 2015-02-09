import argparse
import socket
import sys
import pbots_calc

"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""

class player_counter(object):
    def __init__(self, name):
        self.name = name
        self.hands = 0 
        self.calls = 1 #number of calls, percent calls
        self.per_calls = 0.8
        self.checks = 1 #number of checks, percent checks
        self.per_checks = 0
        self.raises = 1 # number of raises, amount, raises%, amount_avg
        self.per_raises = 0
        self.amt_raise = 0
        self.amt_avg_raise = 0
        self.folds = 1
        self.per_folds=0
        self.aggressionfactor = 0
        self.aggrofreq = 0
      
        self.vpip = 0
        self.per_vpip = 0
        self.pfr = 0
        self.per_pfr = 0

        self.wtsd = 0
        self.per_wtsd = 0
        self.wmsd = 0
        self.per_wmsd = 0 

    def update(self):
        self.per_calls = self.calls/float(self.calls+self.checks+self.folds+self.raises)
        self.per_checks = self.checks/float(self.calls+self.checks+self.folds+self.raises)
        self.per_raises = self.raises/float(self.calls+self.checks+self.folds+self.raises)
        self.amt_avg_raise = self.amt_raise/float(self.raises)
        self.per_folds = self.folds/float(self.calls+self.checks+self.folds+self.raises)
        self.per_vpip = self.vpip/float(self.hands)
        self.per_pfr = self.pfr/float(self.hands)
        self.per_wtsd = self.wtsd/float(self.hands)
        self.per_wmsd = self.per_wmsd/float(self.hands)
        self.aggressionfactor = self.raises/float(self.calls+self.checks)
        self.aggrofreq = self.raises/float(self.calls+self.checks+self.folds+self.raises)


class Player:
    def run(self, input_socket):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()

        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip()
            # If data is None, connection has closed.
            if data == "":
                print "Gameover, engine disconnected."
                s.close()
                return
            
            if data.split()[0] == "NEWGAME":

                player_names = data.split()[1:4]
                player_name = player_names[0]
                player_data = dict()
                player_data[player_names[1]] = player_counter(player_names[1])
                player_data[player_names[2]] = player_counter(player_names[2])

                # Default Params
                play_style_params = dict()
                play_style_params["aggression"] = 1.3 # How lenient should we be in making inoptimal bets to prevent leaking?
                play_style_params["min_odds_call"] = 0.01 # What should the minimum odds of winning be for us to raise?
                play_style_params["min_odds_raise"] = 0.3
                play_style_params["equity_mult"] = 0.8 # What should we decrease our equity by to be more accurate?
                play_style_params["raise_mult"] = 1 # Bet more or less depending on how likely our opponents are to call

            params = parse_input(data)



            if params["word"] == "NEWHAND":
                #print "Current stack", params["stackSizes"][params["playerNum"]]
                print player_name
                play_hand(f_in, params, player_data, play_style_params, player_name)


            # Here is where you should implement code to parse the packets from
            # the engine and act on it. We are just printing it instead.
            

            # When appropriate, reply to the engine with a legal action.
            # The engine will ignore all spurious responses.
            # The engine will also check/fold for you if you return an
            # illegal action.
            # When sending responses, terminate each response with a newline
            # character (\n) or your bot will hang!

            elif params["word"] == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                s.send("FINISH\n")
        # Clean up the socket.
        s.close()

def parse_input(input_line):
    data = input_line.split()
    info = {"word":data[0]}

    if data[0] == "GETACTION":

        info["potSize"] = int(data[1])
        info["numBoardCards"] = int(data[2])
        numBoardCards = info["numBoardCards"]
        info["boardCards"] = data[3:3+numBoardCards]
        info["stackSizes"] = map(int, data[3+numBoardCards:6+numBoardCards])
        info["numActivePlayers"] = int(data[6+numBoardCards])
        info["activePlayers"] = map(bool, data[7+numBoardCards:10+numBoardCards])
        info["numLastActions"] = int(data[10+numBoardCards])
        numLastActions = info["numLastActions"]
        info["lastActions"] = data[11+numBoardCards:11+numBoardCards+numLastActions]
        info["numLegalActions"] = int(data[11+numBoardCards+numLastActions])
        numLegalActions = info["numLegalActions"]
        legalActions = data[12+numBoardCards+numLastActions:12+numBoardCards+numLastActions+numLegalActions]
        info["timeBank"] = float(data[-1])

        info["legalActions"] = dict(zip(["BET", "RAISE", "CHECK", "FOLD", "CALL"], [False] * 5))
        for action in legalActions:
            t = action.split(":")

        
            if (t[0] == "BET"):
                info["legalActions"]["BET"] = (int(t[1]), int(t[2]))
            if (t[0] == "RAISE"):
                info["legalActions"]["RAISE"] = (int(t[1]), int(t[2]))
            if (t[0] == "CHECK"):
                info["legalActions"]["CHECK"] = True
            if (t[0] == "FOLD"):
                info["legalActions"]["FOLD"] = True
            if (t[0] == "CALL"):
                info["legalActions"]["CALL"]= int(t[1])


    elif data[0] == "NEWHAND":

        info["handID"] = int(data[1])
        info["seat"] = int(data[2])
        info["hole1"] = data[3]
        info["hole2"] = data[4]
        info["stackSizes"] = map(int, data[5:8])
        info["players"] = data[8:11]
        info["numActivePlayers"] = int(data[11])
        info["activePlayers"] = map(bool, data[12:15])
        info["timeBank"] = float(data[15])

    elif data[0] == "HANDOVER":
        info["stackSizes"] = map(int, data[1:4])
        info["numBoardCards"] = int(data[4])
        numBoardCards = info["numBoardCards"]
        info["boardCards"] = data[5:5+numBoardCards]
        info["numLastActions"] = int(data[5+numBoardCards])
        numLastActions = info["numLastActions"]
        info["lastActions"] = data[6+numBoardCards:6+numBoardCards+numLastActions]
        info["timeBank"] = data[-1]

    return info



def send_action(action, value=None):
    if value:
        s.send(action + ":" + str(value) + "\n")
    else:
        s.send(action + "\n")

def update_player_data(player_data, lastActions, player_name):
    #actions=info["lastActions"]
    actions = lastActions
    try: 
        flop_index = actions.index("DEAL:FLOP")
    except ValueError:
        flop_index = len(actions) + 1
    
    for player in player_data:
        player_data[player].hands += 1

    for i in range(len(actions)):
        play = actions[i].split(":")

        if play[-1] == player_name:
            continue

        if (play[0]=="CALL"):
            if (i < flop_index): #preflop
                player_data[play[-1]].vpip += 1
            player_data[play[-1]].calls += 1
        elif (play[0]=="FOLD"):
           player_data[play[-1]].folds += 1
        elif (play[0]=="CHECKS"):
            player_data[play[-1]].checks += 1
        elif (play[0]=="RAISE" or play[0] == "BET"):
            if (i < flop_index):
                player_data[play[-1]].vpip += 1
                player_data[play[-1]].pfr += 1
            player_data[play[-1]].raises += 1
            player_data[play[-1]].amt_raise += int(play[1])

    for player in player_data:
        player_data[player].update()

def update_play_style_params(player_data, play_style_params):

    updatedaggression = 0.4 + sum([player.per_vpip + player.aggrofreq for _, player in player_data.items()])/4.0

    if sum([player.per_vpip for _, player in player_data.items()]) < sum([player.pfr for _, player in player_data.items()]) < 1.5 * sum([player.per_vpip for _, player in player_data.items()]): #if TAG player
        updated_equity_mult = sum([player.per_pfr/player.per_vpip for _, player in player_data.items()])/2.0
    else:
        updated_equity_mult = play_style_params["equity_mult"]

    updated_raise_mult = 5*sum([player.per_calls for _, player in player_data.items()])/2.0

    play_style_params["aggression"] = play_style_params["aggression"] * .95 + updatedaggression*.05# How lenient should we be in making inoptimal bets to prevent leaking?
    play_style_params["min_odds_call"] = 0.2 # What should the minimum odds of winning be for us to call?
    play_style_params["min_odds_raise"] = 0.3
    play_style_params["equity_mult"] = play_style_params["equity_mult"] * 0.95 + updated_equity_mult*.05 # What should we decrease our equity by to be more accurate?
    play_style_params["raise_mult"] = play_style_params["raise_mult"] * .95 + updated_raise_mult*.05 # Bet more or less depending on how likely our opponents are to call

def calculate_desired_raise(min_wager, current_pot, current_stack, equity, player_data, 
    next_players, play_style_params, reraise, numActivePlayers):
    #predicted_pot = current_pot + min_wager + calculate_predicted_pot_increase(min_wager, 
     #                                               player_data, next_players, reraise)

    kelly_wealth = current_stack + current_pot + calculate_predicted_pot_increase(min_wager, player_data, next_players, reraise)/numActivePlayers

    kelly_criterion = float((equity * numActivePlayers) - 1)/(numActivePlayers - 1)

    ideal_kelly_pot = kelly_criterion * kelly_wealth #pot odds based on money

    kelly_bet = ideal_kelly_pot - current_pot

    #for i in xrange(5):
     #   kelly_wealth = current_stack + current_pot + calculate_predicted_pot_increase(kelly_bet, player_data, next_players, reraise)/numActivePlayers
      #  ideal_kelly_pot = kelly_criterion * kelly_wealth #pot odds based on money
       # kelly_bet = ideal_kelly_pot - current_pot

    #desired_raise = kelly_bet + min_wager
    desired_raise = kelly_bet

    print desired_raise

    return desired_raise


# NOT ACCOUNTING FOR EVERYBODY ELSE. 
def calculate_predicted_pot_increase(bet, player_data, players_left, reraise):
    if reraise[0]:
        bet = bet - reraise[1]
    increase = bet
    for player in players_left:
        increase += bet * player.per_calls
    return increase

def play_hand(socket_file, hand_params, player_data, play_style_params, our_player_name):

    print hand_params["handID"], "handID"
    print play_style_params

    hole_cards = hand_params["hole1"] + hand_params["hole2"]
    seat = hand_params["seat"]
    reraise = [False, 0, None] # Was there a reraise? last wager, turn
    while True:
        packet = socket_file.readline().strip()
        if packet == "":
    #            print "Gameover, engine disconnected."
                return

        data = parse_input(packet)

        if data["word"] == "GETACTION":

            current_pot = data["potSize"]
            minimum_wager = data["legalActions"]["CALL"] or 0
            turns_left = {0:4, 3:3, 4:2, 5:1}[data["numBoardCards"]]

            if reraise[2] == turns_left:
                reraise[0] = True
            else:
                reraise[0] = False
                reraise[2] = turns_left

            next_players = []
            if turns_left == 4:
                next_players = [player_data[player_name] for player_name, isActive in zip(hand_params["players"], data["activePlayers"])[seat:] if isActive]
            else: 
                if seat == 1:
                    next_players = []
                elif seat == 2:
                    next_players = [player_data[player_name] for player_name, isActive in zip(hand_params["players"], data["activePlayers"])[0:3:2] if isActive]
                else:
                    next_players = [player_data[player_name] for player_name, isActive in [zip(hand_params["players"], data["activePlayers"])[0]] if isActive]

            if current_pot <= 6 and turns_left == 4:
                evaluation_string = hole_cards + ":xx" * (hand_params["numActivePlayers"] - 1)
                equity = pbots_calc.calc(evaluation_string, "","", 5000).ev[0]

                predicted_pot = 6
                #next_players = [player_data[player_name] for player_name in hand_params["players"][seat:]]

            else:
                evaluation_string = hole_cards + ":xx" * (hand_params["numActivePlayers"] - 1)
                equity = pbots_calc.calc(evaluation_string, "","", 5000).ev[0] * play_style_params["equity_mult"]

                predicted_pot = current_pot + calculate_predicted_pot_increase(minimum_wager, player_data, next_players, reraise)

            # Net expected profit < 0? Fold. 

            if reraise[0]:
                if (minimum_wager-reraise[1] > predicted_pot * equity * play_style_params["aggression"]) or \
                        (equity <= play_style_params["min_odds_call"]):
                    reraise[1] = 0
                    send_action("FOLD")
                    continue
            else:
                if (minimum_wager > predicted_pot * equity * play_style_params["aggression"]) or \
                        (equity <= play_style_params["min_odds_call"]):
                    reraise[1] = 0
                    send_action("FOLD")
                    continue


            current_stack = data["stackSizes"][seat-1]


            BET_or_RAISE = "RAISE" if data["legalActions"]["RAISE"] != False else "BET"

            if data["legalActions"][BET_or_RAISE] == False:
                reraise[1] = minimum_wager
                send_action("CALL", minimum_wager)
                continue

            if equity <= play_style_params["min_odds_raise"]:
                if data["legalActions"]["CHECK"]:
                    reraise[1] = 0
                    send_action("CHECK")
                    continue
                else:
                    reraise[1] = minimum_wager
                    send_action("CALL", minimum_wager)
                    continue

            desired_raise = calculate_desired_raise(minimum_wager, current_pot, current_stack, 
                equity, player_data, next_players, play_style_params, reraise, data["numActivePlayers"])

            minimum_raise, maximum_raise = data["legalActions"][BET_or_RAISE]

            if desired_raise <= minimum_raise:
                if data["legalActions"]["CHECK"]:
                    reraise[1] = 0
                    send_action("CHECK")
                    continue
                else:
                    reraise[1] = minimum_wager
                    send_action("CALL", minimum_wager)
                    continue

            desired_raise = max(min(maximum_raise, desired_raise/turns_left), 0) * play_style_params["raise_mult"]

            reraise[1] = desired_raise
            send_action(BET_or_RAISE, desired_raise)


        
        if data["word"] == "HANDOVER":

            update_player_data(player_data, data["lastActions"], our_player_name)
            update_play_style_params(player_data, play_style_params)
            # Hand over
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    print 'Connecting to %s:%d' % (args.host, args.port)
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        print 'Error connecting! Aborting'
        exit()

    bot = Player()
    bot.run(s)
