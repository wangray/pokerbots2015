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

class otherPlayer(object):
    def __init__(self, name):
        self.name = name
        self.checks = 0
        self.raises = 0
        self.avg_raise = 0
        self.folds = 0
        self.aggresiveness = 0

MYNAME = ""

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
                global MYNAME
                MYNAME = data.split()[1]

            params = parse_input(data)

            if params["word"] == "NEWHAND":
                params["aggr1"] = 1.05 # How lenient should we be in making inoptimal bets?
                params["aggr2"] = 0.3 # What should the minimum odds of winning be for us to raise?
                params["aggr3"] = 0.6 # What is the probability that opponents call?

                #print "Current stack", params["stackSizes"][params["playerNum"]]
                play_hand_2(f_in, params)



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
        info["playerNum"] = info["players"].index(MYNAME)

    return info


# def play_hand(socket_file, params):

#     # RE-RAISES AREN'T COUNTED AS RE-RAISING!

#     print params["handID"]
#     print params["timeBank"]
#     hole_cards = params["hole1"] + params["hole2"]
#     while True:
#         data = socket_file.readline().strip()
#         if data == "":
#                 print "Gameover, engine disconnected."
#                 return

#         info = parse_input(data)

#         if info["word"] == "GETACTION":

#             extra_str = ":xx" * (info["numActivePlayers"]-1)
#             odds_winning = pbots_calc.calc(hole_cards + extra_str, "".join(info["boardCards"]), "", 5000).ev[0]
#             global CALLED_EVALUATOR
#             CALLED_EVALUATOR += 1
#             current_stack = info["stackSizes"][params["playerNum"]]

#             pot_size = info["potSize"]
#             call_amount = info["legalActions"]["CALL"] or 0
#             players_left_this_round = sum(info["activePlayers"][params["playerNum"]:])
#             possible_action = "BET" if info["legalActions"]["BET"] != False else "RAISE"


#             if odds_winning * (pot_size + (call_amount * players_left_this_round)) * params["aggr1"] <= call_amount:
#                 # Should default to FOLD
#                 s.send("CHECK\n")

#             #Slightly buggy - should fix. Might be betting slightly less than optimal. 

#             #kelly_criterion = float(odds_winning*(net_odds + 1) - 1)/net_odds
#             kelly_criterion = float((odds_winning * info["numActivePlayers"]) - 1)/(info["numActivePlayers"] - 1)

#             kelly_bet_unrestricted = int(kelly_criterion * current_stack)

#             # turns_left = {0:4, 3:3, 4:2, 5:1}[info["numBoardCards"]]

#             # actions_left = players_left_this_round + info["numActivePlayers"] * turns_left

#             # kelly_bet = max(0, optimal_pot - call_amount - pot_size)/float(actions_left)


#             kelly_bet = max(0, kelly_bet_unrestricted - call_amount)


#             try: 
#                 min_bet, max_bet = info["legalActions"][possible_action]
#             except TypeError:
#                 s.send("CALL:" + str(call_amount) + "\n")
#                 continue



#             kelly_bet = min(kelly_bet - call_amount, max_bet)

#             if (kelly_bet < min_bet/2) or (odds_winning < params["aggr2"]):
#                 if info["legalActions"]["CALL"] == False:
#                     s.send("CHECK\n")
#                 else:
#                     s.send("CALL:" + str(call_amount) + "\n")
#             else:
#                 s.send(possible_action + ":" + str(int(call_amount + kelly_bet)) + "\n")
        
#         if info["word"] == "HANDOVER":
#             print CALLED_EVALUATOR, " EVALUATOR_CALLS"
#             # Hand over
#             return

def send_action(action, value=None):
    if value:
        s.send(action + ":" + str(value) + "\n")
    else:
        s.send(action + "\n")

def play_hand_2(socket_file, hand_params):
    # print
    # print 
    print hand_params["handID"], "Hand ID"
    print hand_params["timeBank"]
    print hand_params["stackSizes"][hand_params["playerNum"]], "Current Stack Size"
    hole_cards = hand_params["hole1"] + hand_params["hole2"]
    print hole_cards
    old_turns_left = 0
    prev_raise = 0

    while True:
        packet = socket_file.readline().strip()
        if packet == "":
    #            print "Gameover, engine disconnected."
                return

        data = parse_input(packet)

        if data["word"] == "GETACTION":
            
            same_turn = False
            turns_left = {0:4, 3:3, 4:2, 5:1}[data["numBoardCards"]]
            if turns_left == old_turns_left:
                same_turn = True

            if not same_turn:
                prev_raise = 0 

            old_turns_left = turns_left

            numActivePlayers = data["numActivePlayers"]
            minimum_wager = data["legalActions"]["CALL"] or 0
            playerNum = hand_params["playerNum"]
            #players_left_this_round = {0:1, 1:3, 2:2}[playerNum]

            if playerNum == 0:
                players_left_this_round = 1
            elif playerNum == 1:
                players_left_this_round = sum(data["activePlayers"])
            elif playerNum == 2:
                players_left_this_round = 1 + data["activePlayers"][2]

            pot_size = data["potSize"]
            current_stack = data["stackSizes"][playerNum]

            # Different order
            if turns_left == 4:
                effective_pot = max(numActivePlayers * 2, minimum_wager * numActivePlayers)
                # print "effective pot", effective_pot
                # print data["legalActions"]
                #odds_winning = lookup_odds(hole_cards)
                extra_str = ":xx" * (numActivePlayers - 1)
                odds_winning = pbots_calc.calc(hole_cards + extra_str, "", "", 5000).ev[0]
            else: 
                effective_pot = pot_size + minimum_wager * players_left_this_round #+ minimum_wager * (players_left_this_round - 1) * hand_params["aggr3"]
                extra_str = ":xx" * (numActivePlayers - 1)
                odds_winning = pbots_calc.calc(hole_cards + extra_str, "".join(data["boardCards"]), "", 5000).ev[0]

            #print odds_winning, "odds_winning"

            BET_or_RAISE = "BET" if data["legalActions"]["BET"] else "RAISE"

            # Check if call is profitable
            #if float(minimum_wager)/effective_pot > odds_winning * hand_params["aggr1"]:
             #   print "FOLD"
              #  send_action("FOLD")

            if (float(minimum_wager-prev_raise) > effective_pot * odds_winning * hand_params["aggr1"]):
                print data["legalActions"]
                print "FOLD1"
                send_action("FOLD")
                continue

            # We should not be folding here
            kelly_wealth = max(current_stack, 150) + effective_pot/numActivePlayers

            kelly_criterion = float((odds_winning * numActivePlayers) - 1)/(numActivePlayers - 1)

            ideal_kelly_pot = kelly_criterion * kelly_wealth
            print "ideal_kelly_pot", ideal_kelly_pot
            print "pot_size", pot_size
            amount_needed_to_raise = ideal_kelly_pot - pot_size

            print "minimum_wager-prev_raise", minimum_wager-prev_raise
            print "amount_needed_to_raise: ", amount_needed_to_raise, 
            print "odds_winning: ", odds_winning


            #if (float(minimum_wager-prev_raise) > 3 * amount_needed_to_raise) and odds_winning < .75 and minimum_wager > 10:
            if (-amount_needed_to_raise > pot_size/2.0 and odds_winning < 0.85 and minimum_wager > 10):    
                print data["legalActions"]
                print "FOLD2"
                send_action("FOLD")
                continue



            try:
                minimum_raise, maximum_raise = data["legalActions"][BET_or_RAISE]
            except TypeError:
                if current_stack <= 3:
                    if minimum_wager == 0:
                        print data["legalActions"]
                        print "CHECK1"
                        send_action("CHECK")
                    else:
                        print data["legalActions"]
                        print "CALL1", minimum_wager
                        send_action("CALL", minimum_wager)
                        prev_raise = minimum_wager
                    return
                minimum_raise, maximum_raise = 0, 0


            wanted_raise_this_turn = int(max(min(amount_needed_to_raise/(turns_left * numActivePlayers), maximum_raise), 0))

            if (wanted_raise_this_turn - minimum_wager <= minimum_raise) or \
                (odds_winning < hand_params["aggr2"]) or ((data["legalActions"][BET_or_RAISE] == False) and (minimum_wager == 0)):
                if minimum_wager == 0:
                    print data["legalActions"]
                    print "CHECK2"
                    send_action("CHECK")
                else:
                    print data["legalActions"]
                    print "CALL2", minimum_wager
                    send_action("CALL", minimum_wager)
                    prev_raise = minimum_wager

                continue
            else:
                if maximum_raise == 0:
                    if minimum_wager == 0:
                        print data["legalActions"]
                        print "CHECK3"
                        send_action("CHECK")
                    else:
                        print data["legalActions"]
                        print "CALL3", minimum_wager
                        send_action("CALL", minimum_wager)
                        prev_raise = minimum_wager
                    continue

                final_submit = min(maximum_raise, wanted_raise_this_turn)
                print data["legalActions"]
                print "BET_or_RAISE1", final_submit

                send_action(BET_or_RAISE, final_submit)
                prev_raise = final_submit

        
        if data["word"] == "HANDOVER":
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
